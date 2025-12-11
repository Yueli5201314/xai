import flet as ft
import httpx
import json
import os  # 新增：用来读取环境变量


def main(page: ft.Page):
    # --- 1. 网页版专属配置 ---
    page.title = "Grok Desktop"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"

    # 这一行很重要：适配手机屏幕
    page.adaptive = True

    # --- 2. 获取 API Key (安全版) ---
    # 在本地运行时，如果找不到环境变量，请确保你在电脑上设置了，或者暂时在这里写死测试
    # 在 Render 服务器上，我们会专门设置这个变量
    API_KEY = os.environ.get("XAI_API_KEY")

    if not API_KEY:
        page.add(ft.Text("❌ 错误：未配置 API Key，请检查服务器环境变量。", color="red"))
        return

    # --- 下面是之前的 UI 和逻辑代码，基本不用动 ---
    chat_list = ft.ListView(expand=True, spacing=15, auto_scroll=True)

    txt_input = ft.TextField(
        hint_text="Ask Grok...",
        bgcolor="#111111",
        border_color="#333333",
        color="white",
        border_radius=15,
        multiline=True,
        min_lines=1,
        max_lines=5,
        expand=True,
        shift_enter=True,
    )

    def send_message(e):
        user_text = txt_input.value
        if not user_text:
            return

        txt_input.value = ""
        txt_input.disabled = True
        page.update()

        chat_list.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Text(user_text, size=15, color="white"),
                    bgcolor="#222222",
                    padding=15,
                    border_radius=15,
                    maw=300,
                )
            ], alignment=ft.MainAxisAlignment.END)
        )
        page.update()

        ai_response_text = ft.Text("Thinking...", size=15, color="grey", font_family="monospace")
        chat_list.controls.append(
            ft.Row([ft.Container(content=ai_response_text, padding=0, maw=350)], alignment=ft.MainAxisAlignment.START)
        )
        page.update()

        full_response = ""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            }
            payload = {
                "model": "grok-4-1-fast-reasoning",
                "messages": [
                    {"role": "system", "content": "You are Grok."},
                    {"role": "user", "content": user_text}
                ],
                "stream": True
            }

            with httpx.stream("POST", "https://api.x.ai/v1/chat/completions", headers=headers, json=payload,
                              timeout=60) as response:
                if response.status_code != 200:
                    ai_response_text.value = f"Error: {response.status_code} - {response.text}"
                else:
                    ai_response_text.value = ""  # 清空 Thinking
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                content = chunk['choices'][0]['delta'].get('content', '')
                                full_response += content
                                ai_response_text.value = full_response + "▌"
                                page.update()
                            except:
                                pass
            ai_response_text.value = full_response

        except Exception as err:
            ai_response_text.value = f"Error: {err}"
            ai_response_text.color = "red"

        txt_input.disabled = False
        txt_input.focus()
        page.update()

    send_btn = ft.IconButton(
        icon="arrow_upward",
        icon_color="black",
        bgcolor="white",
        on_click=send_message
    )
    txt_input.on_submit = send_message

    page.add(
        ft.Column(
            [
                ft.Container(content=ft.Text("Grok", size=20, weight="bold", color="white"),
                             alignment=ft.alignment.center),
                chat_list,
                ft.Divider(color="#333333"),
                ft.Row([txt_input, send_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            expand=True,
        )
    )


# --- 3. 关键修改：适配 Render 服务器端口 ---
if __name__ == "__main__":
    # 从 Render 环境变量获取端口，默认 8080
    port = int(os.environ.get("PORT", 8080))
    # host="0.0.0.0" 意味着允许外网访问
    ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0")