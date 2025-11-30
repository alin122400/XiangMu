from note_assistant import NoteAssistant

assistant = NoteAssistant()

print("📝 智能笔记助手测试程序")
print("示例：")
print("  记录：今天项目需要提交报告")
print("  搜索 项目")
print("  总结笔记")
print("  删除最后一条笔记\n")

while True:
    q = input("你： ")

    if q.lower() == "quit":
        print("退出。")
        break

    result = assistant.process(q)
    print("助手：", result)
    print()
