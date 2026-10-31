"""Offline rebuild from existing narration assets. Does not call a paid TTS API."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
om=Path('D:/CODEX/huashu-motion/cli/om.js')
def run(*args):subprocess.run([str(a) for a in args],check=True)
run(sys.executable,root/'tools/prepare.py')
run(sys.executable,root/'tools/build.py')
run('node',om,'voice',root,'--audio',root/'assets/full-voice.wav','--text',root/'narration.txt','--asr','off')
run('node',om,'check',root,'--samples','24')
run('node',om,'sound',root)
run('node',om,'render',root,'--workers','6')
