#!/usr/bin/env python3
import json
import time
import signal
import sys
from datetime import datetime
from colorama import Fore, Style, init
from websocket import WebSocketApp

init(autoreset=True)

class TestClient:
    def __init__(self, repo_url: str, commits: list):
        self.ws_url = "ws://brain.obimadu.pro/ws"
        self.repo_url = repo_url
        self.commits = commits
        self.results = []
        self.current_commit = None
        self.start_time = None
        self.ws = None
        self.spinner = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        self.spinner_idx = 0

    def print_header(self):
        print(f"\n{Fore.CYAN}🚀 WebSocket Test Client")
        print(f"{Fore.YELLOW}► Repo: {Style.RESET_ALL}{self.repo_url}")
        print(f"{Fore.YELLOW}► Commits: {Style.RESET_ALL}{len(self.commits)}")
        print(f"{Fore.YELLOW}► Server: {Style.RESET_ALL}{self.ws_url}")
        print(f"\n{Fore.MAGENTA}⚡ Press Ctrl+C to exit\n")

    def show_spinner(self):
        self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner)
        return f"{Fore.CYAN}{self.spinner[self.spinner_idx]}"

    def send_next(self):
        if self.commits:
            self.current_commit = self.commits.pop(0)
            self.start_time = time.time()
            msg = {
                "userId": "user-123",
                "chatId": "chat-456",
                "repoURL": self.repo_url,
                "commitHash": self.current_commit,
                "projectType": "fastapi"
            }
            self.ws.send(json.dumps(msg))
            print(f"{Fore.WHITE}📤 Sent: {Fore.YELLOW}{self.current_commit[:7]}")

    def on_open(self, ws):
        print(f"{Fore.GREEN}✅ Connected to server")
        self.send_next()

    def on_message(self, ws, message):
        response_time = time.time() - self.start_time
        try:
            response = json.loads(message)
            status = response.get("type", "unknown")
            
            # Store result
            self.results.append({
                "commit": self.current_commit,
                "status": status,
                "time": response_time,
                "response": response
            })

            # Print response details
            print(f"\n{Fore.WHITE}─── Response for {Fore.YELLOW}{self.current_commit[:7]} " +
                  f"{Fore.WHITE}({response_time:.2f}s) {'─'*40}")
            self.print_response(response)
            
            # Send next commit
            self.send_next()

        except json.JSONDecodeError:
            print(f"{Fore.RED}❌ Invalid JSON response")
            print(f"{Fore.WHITE}Raw message: {message}")

    def print_response(self, response):
        status_color = Fore.GREEN if response.get("type") == "test_results" else Fore.RED
        print(f"{status_color}Status: {response.get('type', 'unknown')}")
        
        # Print formatted JSON
        print(f"{Fore.CYAN}┌{'─'*60}┐")
        formatted_json = json.dumps(response, indent=2)
        for line in formatted_json.split('\n'):
            print(f"{Fore.CYAN}│ {Fore.WHITE}{line}")
        print(f"{Fore.CYAN}└{'─'*60}┘")

    def on_error(self, ws, error):
        print(f"\n{Fore.RED}🚨 Error: {error}")

    def on_close(self, ws, status, msg):
        print(f"\n{Fore.CYAN}🔌 Connection closed")
        self.print_summary()

    def print_summary(self):
        print(f"\n{Fore.CYAN}📊 Test Summary")
        print(f"{Fore.YELLOW}┌{'─'*78}┐")
        
        total = len(self.results)
        success = sum(1 for r in self.results if r["status"] == "test_results")
        avg_time = sum(r["time"] for r in self.results) / total if total > 0 else 0
        
        print(f"{Fore.YELLOW}│ {Fore.WHITE}Total: {total:<4} " +
              f"{Fore.GREEN}Success: {success:<4} " +
              f"{Fore.RED}Failed: {total - success:<4} " +
              f"{Fore.WHITE}Avg Time: {avg_time:.2f}s")
        
        print(f"{Fore.YELLOW}├{'─'*78}┤")
        for result in self.results:
            color = Fore.GREEN if result["status"] == "test_results" else Fore.RED
            print(f"{Fore.YELLOW}│ {color}◼ {result['commit'][:7]} " +
                  f"{Fore.WHITE}{result['time']:.2f}s " +
                  f"{color}{result['status']}")
        
        print(f"{Fore.YELLOW}└{'─'*78}┘\n")

    def run(self):
        self.print_header()
        self.ws = WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
        self.ws.run_forever()

    def shutdown(self):
        print(f"\n{Fore.RED}🛑 Shutting down...")
        self.ws.close()
        self.print_summary()
        sys.exit(0)

if __name__ == "__main__":
    commits = [
        "2acf0f9a74b83bc881aa2f06235b8c927892d28a",
        "invalidcommit1234567890abcdefghijklmnop",
        "d0d0caca1bcd1234abcd5678efab1234cafed00d"
    ]
    
    client = TestClient(
        repo_url="https://github.com/obiMadu/hng12-stage2",
        commits=commits
    )
    client.run()
