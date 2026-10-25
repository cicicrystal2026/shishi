"""Shishi's loopback-only HTTP bridge, not an official IndexTTS HTTP API."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def make_server(engine, reference, cache, port=9880, version='2.5'):
    cache = Path(cache).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Do not log narration, voice samples, or request bodies.

        def send_json(self, status, payload):
            data = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path != '/health':
                return self.send_json(404, {'error': 'NOT_FOUND'})
            return self.send_json(200, {'service': 'shishi-index-tts', 'ready': True,
                                       'model': 'IndexTTS-' + version,
                                       'referenceReady': bool(reference and Path(reference).is_file())})

        def do_POST(self):
            if self.path != '/v1/audio/speech':
                return self.send_json(404, {'error': 'NOT_FOUND'})
            # Browser cross-site calls are not supported; Shishi's backend sends no Origin.
            if self.headers.get('Origin'):
                return self.send_json(403, {'error': 'ORIGIN_DENIED'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 12 * 1024 * 1024:
                    return self.send_json(413, {'error': 'PAYLOAD_LIMIT'})
                data = json.loads(self.rfile.read(length))
                text = data.get('input', '')
                if not isinstance(text, str) or not text.strip() or len(text) > 3000:
                    return self.send_json(400, {'error': 'INVALID_TEXT'})
                speed = float(data.get('duration_factor', 1))
                if not 0.5 <= speed <= 2:
                    return self.send_json(400, {'error': 'INVALID_SPEED'})
                raw = data.get('reference_audio')
                audio = base64.b64decode(raw, validate=True) if raw else None
                if audio and (len(audio) > 8 * 1024 * 1024 or audio[:4] != b'RIFF' or audio[8:12] != b'WAVE'):
                    return self.send_json(400, {'error': 'INVALID_REFERENCE_WAV'})
                if not audio and not (reference and Path(reference).is_file()):
                    return self.send_json(400, {'error': 'REFERENCE_REQUIRED'})
                refhash = hashlib.sha256(audio if audio else Path(reference).read_bytes()).hexdigest()
                digest = hashlib.sha256(json.dumps([text, speed, refhash, version], ensure_ascii=False).encode()).hexdigest()
                target = cache / (digest + '.wav')
                with lock:
                    if not target.exists():
                        with tempfile.TemporaryDirectory(dir=cache) as temp:
                            source = reference
                            if audio:
                                source = str(Path(temp) / 'reference.wav')
                                Path(source).write_bytes(audio)
                            output = str(Path(temp) / 'result.wav')
                            kwargs = dict(spk_audio_prompt=str(source), text=text, output_path=output, verbose=False)
                            if version == '2.5':
                                kwargs.update(lang='ZH', duration_factor=speed)
                            engine.infer(**kwargs)
                            result = Path(output).read_bytes()
                            if result[:4] != b'RIFF' or result[8:12] != b'WAVE':
                                raise RuntimeError('INVALID_OUTPUT_WAV')
                            Path(output).replace(target)
                result = target.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'audio/wav')
                self.send_header('Content-Length', str(len(result)))
                self.send_header('X-Request-Id', digest)
                self.end_headers()
                self.wfile.write(result)
            except (ValueError, TypeError, json.JSONDecodeError):
                self.send_json(400, {'error': 'INVALID_REQUEST'})
            except Exception as exc:
                # Only the error type is public, not filesystem paths or narration.
                print('IndexTTS synthesis failed:', type(exc).__name__, flush=True)
                self.send_json(500, {'error': 'SYNTHESIS_FAILED'})

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--model-dir', required=True)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--cache', required=True)
    parser.add_argument('--port', type=int, default=9880)
    parser.add_argument('--version', choices=['2', '2.5'], default='2.5')
    args = parser.parse_args()
    repo, models, reference = (Path(p).resolve() for p in (args.repo, args.model_dir, args.reference))
    if not (models / 'config.yaml').is_file() or not reference.is_file():
        parser.error('Model config or reference audio missing; download resources before starting.')
    os.chdir(repo)
    sys.path.insert(0, str(repo))
    # Transformers 4.50+ no longer mixes generation methods into the GPT2 base.
    # Apply the upstream warning's narrow compatibility remedy in this process only.
    from indextts.gpt import model_v2
    from transformers.generation import GenerationMixin
    if not issubclass(model_v2.GPT2InferenceModel, GenerationMixin):
        class ShishiGPT2InferenceModel(model_v2.GPT2InferenceModel, GenerationMixin):
            pass
        model_v2.GPT2InferenceModel = ShishiGPT2InferenceModel
    if args.version == '2.5':
        from indextts.infer_v2_5 import IndexTTS2
        engine = IndexTTS2(cfg_path=str(models / 'config.yaml'), model_dir=str(models), use_bf16=True, use_cuda_kernel=False, use_deepspeed=False, use_qwen_emo=False)
    else:
        from indextts.infer_v2 import IndexTTS2
        engine = IndexTTS2(cfg_path=str(models / 'config.yaml'), model_dir=str(models), use_fp16=True,
                           use_cuda_kernel=False, use_deepspeed=False)
    server = make_server(engine, reference, args.cache, args.port, args.version)
    print(f'IndexTTS ready: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
