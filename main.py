import flet as ft
import httpx
import json
import os
import sys

# 强制打印日志到控制台
def log(msg):
    print(f"[DEBUG] {msg}", file=sys.stdout, flush=True)

def main(page: ft.Page):
    page.title = "Grok Debug"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.adaptive = True

    # 1. 打印检查 API Key 是否真的读取到了
    api_key = os.environ.get("XAI_API_KEY")
    if api_key:
        log(f"API Key loaded. Length: {len(api_key)}")
        log(f"Key starts with: {api_key[:4]}...")
    else:
        log("CRITICAL: API Key is MISSING or Empty!")

    chat_list = ft.ListView(expand=True, spacing=15, auto_scroll=True)
    txt_input = ft.TextField(hint_text="Type something...", bgcolor="#111111", color="white", expand=True)

    def send_message(e):
        user_text = txt_input.value
        if not user_text: return

        log(f"User sending message: {user_text}") # 打印用户输入

        txt_input.value = ""
        txt_input.disabled = True
        
        chat_list.controls.append(ft.Text(f"You: {user_text}", color="white"))
        
        # 状态指示器
        status_text = ft.Text("Connecting to xAI...", color="yellow")
        chat_list.controls.append(status_text)
        page.update()

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            # ⚠️ 关闭流式，设置超时为 10 秒
            payload = {
                "model": "grok-3",
                "messages": [{"role": "user", "content": user_text}],
                "stream": False 
            }

            log("Sending HTTP request...")
            
            # 发送请求
            response = httpx.post(
                "https://api.x.ai/v1/chat/completions", 
                headers=headers, 
                json=payload, 
                timeout=15.0 # 设置超时，防止无限死等
            )

            log(f"Response Status Code: {response.status_code}")
            log(f"Response Body: {response.text}")

            if response.status_code == 200:
                data = response.json()
                reply = data['choices'][0]['message']['content']
                status_text.value = f"Grok: {reply}"
                status_text.color = "#E0E0E0"
            else:
                # 如果出错，直接把错误码显示在屏幕上
                status_text.value = f"ERROR: {response.status_code}\n{response.text}"
                status_text.color = "red"

        except Exception as err:
            log(f"EXCEPTION: {err}")
            status_text.value = f"CRASH: {err}"
            status_text.color = "red"

        txt_input.disabled = False
        txt_input.focus()
        page.update()

    send_btn = ft.IconButton(icon="arrow_upward", on_click=send_message)
    
    page.add(
        ft.Column([
            chat_list,
            ft.Row([txt_input, send_btn]),
        ], expand=True)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0")
