from openai import OpenAI
import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import json

with st.sidebar:
    openai_api_key = st.text_input("画图 API Key", key="chatbot_api_key", type="password", value="sk-jHgGewhUPLMCansI6981EcBb5d564dD28dE7E6A88b420629")
    "[咸鱼购买](https://m.tb.cn/h.6dyAE1n?tk=L3wXeFQXd6b)"

st.title("🚀 快速体验GPT 4o画图能力")
st.caption("最近比较火热，如果生成失败可以刷新重试")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "描述图片"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input(placeholder="描述图片"):
    if not openai_api_key:
        st.info("请填写API key")
        st.stop()

    client = OpenAI(api_key=openai_api_key, base_url="https://one.opengptgod.com/v1")
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # 创建进度条和消息占位符
    progress_bar = st.progress(0)
    message_placeholder = st.empty()
    image_placeholder = st.empty()
    full_response = ""
    json_content = ""
    is_collecting_json = False
    final_image_url = None
    
    print("\n=== API请求开始 ===")
    print(f"用户输入: {prompt}")
    
    # 使用流式输出
    stream = client.chat.completions.create(
        model="gpt-4o-image",
        messages=st.session_state.messages,
        stream=True
    )
    
    # 逐步显示响应
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            chunk_content = chunk.choices[0].delta.content
            print(f"收到内容: {chunk_content}")
            
            # 处理JSON内容
            if chunk_content.strip().startswith("{"):
                is_collecting_json = True
            
            if is_collecting_json:
                json_content += chunk_content
                try:
                    # 尝试解析JSON
                    json.loads(json_content)
                    is_collecting_json = False
                    print("JSON配置:", json_content)
                    continue
                except json.JSONDecodeError:
                    # JSON还不完整，继续收集
                    continue
            
            full_response += chunk_content
            
            # 检查是否包含进度URL
            if "[" in chunk_content and "]" in chunk_content and "http" in chunk_content:
                try:
                    # 提取URL
                    start_idx = chunk_content.find("http")
                    end_idx = chunk_content.find(")", start_idx)
                    if end_idx == -1:
                        end_idx = len(chunk_content)
                    url = chunk_content[start_idx:end_idx]
                    final_image_url = url  # 保存最后一个URL
                    print(f"\n检测到进度URL: {url}")
                except Exception as e:
                    error_msg = f"URL提取失败: {str(e)}"
                    print(error_msg)
            
            # 更新文本显示
            message_placeholder.write(full_response)
    
    # 生成完成后，只显示最终图片
    if final_image_url:
        try:
            response = requests.get(final_image_url)
            img = Image.open(BytesIO(response.content))
            image_placeholder.image(img, caption="生成的图片")
            print("最终图片加载成功")
        except Exception as e:
            error_msg = f"最终图片加载失败: {str(e)}"
            print(error_msg)
            st.error(error_msg)
    
    print("\n=== 完整响应 ===")
    print(full_response)
    print("\n=== API请求结束 ===")
    
    final_display = full_response.replace(json_content, "").strip()
    message_placeholder.write(final_display)
    st.session_state.messages.append({"role": "assistant", "content": final_display})
    progress_bar.empty()
