"""Small JSON-RPC client for isolated Codex app-server sessions."""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path


def codex_binary():
    override = os.environ.get("EVAL_CODEX_BINARY")
    if override:
        return override
    bundled = Path(os.environ["LOCALAPPDATA"]) / "OpenAI/Codex/bin"
    installed = list(bundled.glob("*/codex.exe"))
    if installed:
        return str(max(installed, key=lambda p: p.stat().st_mtime))
    root = Path(os.environ["APPDATA"]) / "npm/node_modules/@openai/codex"
    matches = list(root.glob("node_modules/@openai/codex-*/vendor/*/bin/codex.exe"))
    if not matches:
        raise RuntimeError("Set EVAL_CODEX_BINARY to the native Codex executable")
    return str(matches[0])


class CodexRPC:
    def __init__(self, runtime):
        self.runtime = runtime
        self.pending = {}
        self.queues = {}
        self.handlers = {}
        self.counter = 0
        self.stderr = []

    async def __aenter__(self):
        self.home = Path(tempfile.mkdtemp(prefix="codex-", dir=self.runtime))
        try:
            return await self._start()
        except BaseException:
            await self.close()
            raise

    async def _start(self):
        original = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        auth = original / "auth.json"
        if auth.exists():
            shutil.copyfile(auth, self.home / "auth.json")
        env = dict(os.environ, CODEX_HOME=str(self.home))
        flags = {"features.shell_tool": False, "features.apply_patch_freeform": False,
                 "features.js_repl": False, "features.multi_agent": False,
                 "features.apps": False, "features.plugins": False,
                 "features.skills": False, "project_doc_max_bytes": 0,
                 "web_search": "disabled"}
        args = [codex_binary(), "app-server", "--stdio"]
        for key, value in flags.items():
            args += ["-c", f"{key}={json.dumps(value)}"]
        self.process = await asyncio.create_subprocess_exec(
            *args, env=env, cwd=self.runtime, stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        self.reader = asyncio.create_task(self._read())
        self.err_reader = asyncio.create_task(self._read_errors())
        await self.request("initialize", {"clientInfo": {"name": "jev_behavior_evals",
                           "version": "1.0.0"}, "capabilities": {"experimentalApi": True}})
        self.send({"method": "initialized"})
        return self

    def send(self, message):
        self.process.stdin.write((json.dumps(message) + "\n").encode())

    async def request(self, method, params):
        self.counter += 1
        request_id = self.counter
        future = asyncio.get_running_loop().create_future()
        self.pending[request_id] = future
        self.send({"id": request_id, "method": method, "params": params})
        return await asyncio.wait_for(future, 90)

    async def _read(self):
        while line := await self.process.stdout.readline():
            message = json.loads(line)
            if "method" not in message:
                future = self.pending.pop(message.get("id"), None)
                if future and not future.done():
                    if "error" in message:
                        future.set_exception(RuntimeError(json.dumps(message["error"])))
                    else:
                        future.set_result(message.get("result"))
                continue
            params = message.get("params", {})
            thread_id = params.get("threadId", params.get("thread", {}).get("id"))
            if "id" in message:
                asyncio.create_task(self._respond(message, thread_id))
            elif thread_id in self.queues:
                await self.queues[thread_id].put(message)
        for future in self.pending.values():
            if not future.done():
                future.set_exception(RuntimeError("Codex app-server exited"))

    async def _respond(self, message, thread_id):
        if message["method"] == "item/tool/call" and thread_id in self.handlers:
            result = await self.handlers[thread_id](message["params"])
            self.send({"id": message["id"], "result": result})
        else:
            self.send({"id": message["id"], "error": {
                "code": -32601, "message": "Only explicitly supplied evaluation tools are allowed"}})

    async def _read_errors(self):
        while line := await self.process.stderr.readline():
            self.stderr.append(line.decode(errors="replace"))
            self.stderr = self.stderr[-40:]

    async def __aexit__(self, *_):
        await self.close()

    async def close(self):
        try:
            process = getattr(self, "process", None)
            if process and process.returncode is None:
                process.terminate()
                await asyncio.wait_for(process.wait(), 10)
        finally:
            for name in ("reader", "err_reader"):
                task = getattr(self, name, None)
                if task:
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
            if self.home.resolve().parent != self.runtime.resolve():
                raise ValueError("Refusing cleanup outside runtime directory")
            shutil.rmtree(self.home)
