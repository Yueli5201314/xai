import flet as ft
from openai import OpenAI
import os


def main(page: ft.Page):
    # --- 基础设置 ---
    page.title = "Grok App"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.adaptive = True

    # --- 获取 API Key ---
    api_key = os.environ.get("XAI_API_KEY")

    # --- UI 组件 ---
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
        if not user_text: return

        # 1. 锁住输入框
        txt_input.value = ""
        txt_input.disabled = True

        # 2. 显示用户消息
        chat_list.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Text(user_text, color="white"),
                    bgcolor="#222222", padding=15, border_radius=15, maw=300
                )
            ], alignment=ft.MainAxisAlignment.END)
        )
        page.update()

        # 3. 预备 AI 回复框
        response_text = ft.Text("Grok is thinking...", color="yellow", font_family="monospace")
        chat_list.controls.append(
            ft.Row([
                ft.Container(content=response_text, padding=0, maw=350)
            ], alignment=ft.MainAxisAlignment.START)
        )
        page.update()

        # 4. 核心逻辑 (官方 SDK)
        try:
            if not api_key:
                raise Exception("API Key 未配置！请检查 Render 环境变量。")

            client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1",
            )

            stream = client.chat.completions.create(
                model="grok-4-1-fast-reasoning",
                messages=[
                    {"role": "system", "content": "You are Grok."},
                    {"role": "user", "content": user_text}
                ],
                stream=True,
            )

            full_res = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_res += content
                    # 实时更新 UI
                    response_text.value = full_res + "▌"
                    response_text.color = "#E0E0E0"  # 变回正常颜色
                    page.update()

            # 移除光标
            response_text.value = full_res

        except Exception as err:
            # ⚠️ 关键：如果有错误，直接显示在屏幕上，不再石沉大海
            response_text.value = f"❌ Error: {str(err)}"
            response_text.color = "red"
            page.update()

        # 5. 解锁输入
        txt_input.disabled = False
        txt_input.focus()
        page.update()

    # --- 修复图标 Bug 的按钮 ---
    send_btn = ft.IconButton(
        icon="arrow_upward",  # <--- 这里使用了字符串，绝对不会报错
        icon_color="black",
        bgcolor="white",
        on_click=send_message
    )

    txt_input.on_submit = send_message

    page.add(
        ft.Column(
            [
                ft.Container(content=ft.Text("Grok 3", size=20, weight="bold", color="white"),
                             alignment=ft.alignment.center),
                chat_list,
                ft.Divider(color="#333333"),
                ft.Row([txt_input, send_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            expand=True,
        )
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0")