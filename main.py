import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
from io import BytesIO
import os

from arclet.alconna import TextFormatter
from meme_generator.manager import get_memes, get_meme
from meme_generator.exception import MemeGeneratorException, NoSuchMeme

class MemeGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.preview_image = None  # 用于保持预览图的引用
        self.preview_label = None  # 预览图标签
        self.gif_frames_result = None
        self.current_frame_result = None
        self.result_label = None

        self.root.title("表情包生成器")
        w, h = self.root.maxsize()
        self.root.geometry(f"800x600+{w//5}+{h//7}")
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架布局
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧表情列表
        self.setup_meme_list()
        
        # 右侧功能区域
        self.setup_function_area()
        
    def setup_meme_list(self):
        frame = ttk.LabelFrame(self.main_frame, text="表情列表")
        frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 搜索框
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, padx=5, pady=5)
        search_entry.bind("<KeyRelease>", self.filter_memes)

        # 添加Treeview和滚动条
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 垂直滚动条
        yscroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条
        xscroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 列表树
        self.meme_tree = ttk.Treeview(
            tree_frame,
            columns=("keywords",),
            show="headings",
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )
        self.meme_tree.heading("#0", text="名称")
        self.meme_tree.heading("keywords", text="关键词")
        self.meme_tree.pack(fill=tk.BOTH, expand=True)

        
        # 配置滚动条
        yscroll.config(command=self.meme_tree.yview)
        xscroll.config(command=self.meme_tree.xview)
        
        # 绑定选择事件
        self.meme_tree.bind("<<TreeviewSelect>>", self.show_meme_info)
        
        # 加载表情数据
        self.load_meme_list()

    
    def setup_function_area(self):
        self.func_notebook = ttk.Notebook(self.main_frame)
        self.func_notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 详情标签页
        self.setup_info_tab()
        
        # 生成标签页
        self.setup_generate_tab()
    
    def setup_info_tab(self):
        tab = ttk.Frame(self.func_notebook)
        self.func_notebook.add(tab, text="详情")
        
        # 参数数量信息区域
        self.param_frame = ttk.LabelFrame(tab, text="参数要求")
        self.param_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 图片数量标签
        self.image_label = ttk.Label(self.param_frame, text="图片数量: ")
        self.image_label.pack(side=tk.LEFT, padx=10)
        
        # 文本数量标签
        self.text_label = ttk.Label(self.param_frame, text="文本数量: ")
        self.text_label.pack(side=tk.LEFT, padx=10)
        
        # 将预览图区域移到文本区域上方
        self.preview_frame = ttk.LabelFrame(tab, text="模板预览")
        self.preview_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)  # 改为fill=BOTH并expand
        
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(expand=True, fill=tk.BOTH)  # 让标签也填充整个框架
        
        # 详情文本区域放在最后，并限制高度
        self.info_text = tk.Text(tab, wrap=tk.WORD, height=8)  # 设置固定行数
        self.info_text.pack(fill=tk.X, padx=5, pady=5)  # 改为fill=X不扩展
    
    def setup_generate_tab(self):
        tab = ttk.Frame(self.func_notebook)
        self.func_notebook.add(tab, text="生成")
        
        # 图片选择区域
        img_frame = ttk.LabelFrame(tab, text="图片")
        img_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.image_list = tk.Listbox(img_frame, height=5)
        self.image_list.pack(fill=tk.X, padx=5, pady=5)
        
        btn_frame = ttk.Frame(img_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="添加图片", command=self.add_image).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="移除选中", command=self.remove_image).pack(side=tk.LEFT)
        
        # 文字输入区域改为ListBox实现
        text_frame = ttk.LabelFrame(tab, text="文字", height=8)
        text_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 文本列表
        self.text_listbox = tk.Listbox(text_frame)
        self.text_listbox.pack(fill=tk.X, padx=5, pady=5)
        
        # 按钮区域
        btn_frame = ttk.Frame(text_frame)
        btn_frame.pack(fill=tk.X)
        
        # 添加文本按钮
        ttk.Button(btn_frame, text="添加文本", command=self.add_text).pack(side=tk.LEFT)
        
        # 移除文本按钮
        ttk.Button(btn_frame, text="移除选中", command=self.remove_text).pack(side=tk.LEFT)

        # 参数输入区域
        args_frame = ttk.LabelFrame(tab, text="额外参数 <参数名: 参数值>")
        args_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.args_text = tk.Text(args_frame, height=2, wrap=tk.WORD)
        self.args_text.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加示例标签
        example_label = ttk.Label(args_frame, text="示例: {参数名 : 参数值}, 如 {'message': 'helloworld', 'mode': 'loop'}, \n多个参数使用逗号隔开, 单引号和冒号必须是英文字符", foreground="gray")
        example_label.pack(side=tk.LEFT, padx=5)
        
        # 生成按钮
        ttk.Button(tab, text="生成表情", command=self.generate_meme).pack(pady=10)
    
    # 以下是业务逻辑方法实现
    def load_meme_list(self):
        self.meme_tree.delete(*self.meme_tree.get_children())
        for meme in sorted(get_memes(), key=lambda m: m.key):
            self.meme_tree.insert("", tk.END, text=meme.key, values=("/".join(meme.keywords),))
    
    def filter_memes(self, event=None):
        keyword = self.search_var.get().lower()
        # 获取当前所有可见节点（考虑可能已有部分被隐藏）
        current_items = set(self.meme_tree.get_children())
        # 获取完整节点集合（包括可能被隐藏的）
        all_items = set(self.meme_tree.get_children()) | \
                    set(getattr(self, '_hidden_items', set()))
        
        if not keyword:  # 搜索框为空时恢复所有
            for item in all_items - current_items:
                self.meme_tree.reattach(item, "", "end")
            self._hidden_items = set()
        else:  # 执行过滤
            hidden = set()
            for item in all_items:
                data = self.meme_tree.item(item)
                content = f"{data.get('text','')} {' '.join(map(str, data.get('values',[])))}".lower()
                if keyword in content:
                    self.meme_tree.reattach(item, "", "end")
                    # 确保父链可见
                    parent = self.meme_tree.parent(item)
                    while parent:
                        self.meme_tree.reattach(parent, "", "end")
                        parent = self.meme_tree.parent(parent)
                else:
                    self.meme_tree.detach(item)
                    hidden.add(item)
            self._hidden_items = hidden

    def show_meme_info(self, event):
        self.clear_preview() # 每次切换信息进行一次清理
        selected = self.meme_tree.selection()
        if not selected:
            return
        
        meme_key = self.meme_tree.item(selected[0], "text")
        try:
            meme = get_meme(meme_key)
            
            # 更新参数数量显示
            image_num = f"{meme.params_type.min_images}"
            if meme.params_type.max_images > meme.params_type.min_images:
                image_num += f" ~ {meme.params_type.max_images}"
            
            text_num = f"{meme.params_type.min_texts}"
            if meme.params_type.max_texts > meme.params_type.min_texts:
                text_num += f" ~ {meme.params_type.max_texts}"
            
            self.image_label.config(text=f"图片数量: {image_num}")
            self.text_label.config(text=f"文本数量: {text_num}")
            
            # 显示其他详情信息
            info = self.format_meme_info(meme)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, info)

            # 加载预览图
            self.load_preview_image(meme_key)
        except NoSuchMeme:
            messagebox.showerror("错误", f"表情 '{meme_key}' 不存在!")

    def load_preview_image(self, meme_key):
        # 清除之前的预览图和动画
        if hasattr(self, 'gif_animation_id'):
            self.root.after_cancel(self.gif_animation_id)
            del self.gif_animation_id
        if self.preview_image:
            self.preview_label.config(image="")
            self.preview_image = None
        
        # 尝试加载PNG或GIF格式的预览图
        image_path = None
        for ext in [".png", ".gif", ".jpeg"]:
            path = f"images/{meme_key}{ext}"
            if os.path.exists(path):
                image_path = path
                break
        
        if image_path:
            try:
                img = Image.open(image_path)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                if image_path.endswith(".gif"):
                    # 处理GIF动画
                    self.process_gif_animation(img, image_path)
                else:
                    # 静态图片
                    self.preview_image = ImageTk.PhotoImage(img)
                    self.preview_label.config(image=self.preview_image)
            except Exception as e:
                print(f"加载预览图失败: {e}")
                self.preview_label.config(text="加载预览图失败")
        else:
            self.preview_label.config(text="无预览图")

    def process_gif_animation(self, img, image_path):
        try:
            self.gif_frames = []
            self.current_frame = 0
            
            # 提取所有帧
            while True:
                frame = img.copy()
                if img.tile:
                    # 确保帧大小一致
                    frame = frame.resize((300, 300), Image.Resampling.LANCZOS)
                self.gif_frames.append(frame)
                try:
                    img.seek(len(self.gif_frames))
                except EOFError:
                    break
            
            # 开始动画
            if len(self.gif_frames) > 1:
                self.animate_gif()
            else:
                # 单帧GIF
                self.preview_image = ImageTk.PhotoImage(self.gif_frames[0])
                self.preview_label.config(image=self.preview_image)
        except Exception as e:
            print(f"处理GIF动画失败: {e}")


    # gif 图支持
    def animate_gif(self):
        if hasattr(self, 'gif_frames') and hasattr(self, 'current_frame'):
            frame = self.gif_frames[self.current_frame]
            self.preview_image = ImageTk.PhotoImage(frame)
            self.preview_label.config(image=self.preview_image)
            
            self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
            # 根据GIF帧延迟设置动画速度(默认100ms)
            try:
                delay = self.gif_frames[0].info.get('duration', 100)
            except:
                delay = 100
            self.gif_animation_id = self.root.after(delay, self.animate_gif)

    def clear_preview(self):
        if hasattr(self, 'gif_animation_id'):
            self.root.after_cancel(self.gif_animation_id)
            del self.gif_animation_id
        if hasattr(self, 'gif_frames'):
            del self.gif_frames
        if hasattr(self, 'current_frame'):
            del self.current_frame
        if self.preview_image:
            self.preview_label.config(image="")
            self.preview_image = None


    def format_meme_info(self, meme):
        keywords = "、".join([f'"{keyword}"' for keyword in meme.keywords])
        shortcuts = "、".join([f'"{shortcut.humanized or shortcut.key}"' for shortcut in meme.shortcuts])
        tags = "、".join([f'"{tag}"' for tag in sorted(meme.tags)])
        default_texts = ", ".join([f'"{text}"' for text in meme.params_type.default_texts])
        
        args_info = ""
        if args_type := meme.params_type.args_type:
            formater = TextFormatter()
            for option in args_type.parser_options:
                opt = option.option()
                alias_text = (
                    " ".join(opt.requires)
                    + (" " if opt.requires else "")
                    + "│".join(sorted(opt.aliases, key=len))
                )
                args_info += (
                    f"\n  * {alias_text}{opt.separators[0]}"
                    f"{formater.parameters(opt.args)} {opt.help_text}"
                )
        
        return (
            f"表情名：{meme.key}\n"
            + f"关键词：{keywords}\n"
            + (f"快捷指令：{shortcuts}\n" if shortcuts else "")
            + (f"标签：{tags}\n" if tags else "")
            + (f"默认文字：[{default_texts}]\n" if default_texts else "")
            + (f"其他参数：{args_info}" if args_info else "")
        )

    
    def add_image(self):
        files = filedialog.askopenfilenames(title="选择图片文件")
        for file in files:
            self.image_list.insert(tk.END, file)
    
    def remove_image(self):
        selection = self.image_list.curselection()
        if selection:
            self.image_list.delete(selection[0])

    def add_text(self):
        """添加新文本项"""
        text = simpledialog.askstring("输入文本", "请输入文本内容:")
        if text:
            self.text_listbox.insert(tk.END, text)

    def remove_text(self):
        """移除选中文本项"""
        selection = self.text_listbox.curselection()
        if selection:
            self.text_listbox.delete(selection[0])

    
    def generate_meme(self):
        selected = self.meme_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个表情!")
            return
        
        meme_key = self.meme_tree.item(selected[0], "text")
        images = list(self.image_list.get(0, tk.END))
        texts = list(self.text_listbox.get(0, tk.END))
        
        # 解析额外参数
        args_text = self.args_text.get("1.0", tk.END).strip()
        try:
            args = eval(args_text) if args_text else {}
            if not isinstance(args, dict):
                raise ValueError("参数必须是字典格式")
        except Exception as e:
            messagebox.showerror("参数错误", f"参数格式不正确: {e}")
            return
        
        try:
            meme = get_meme(meme_key)
            result = meme(images=images, texts=texts, args=args)
            self.show_generated_meme(result.getvalue())
        except MemeGeneratorException as e:
            messagebox.showerror("生成失败", str(e))


    def show_generated_meme(self, image_data):
        top = tk.Toplevel(self.root)
        top.title("生成结果")
        top.geometry("600x600+200+100")
        
        img = Image.open(BytesIO(image_data))
        
        # 判断是否为GIF
        if img.format == 'GIF':
            # 处理GIF动画
            self.gif_frames_result = []
            self.current_frame_result = 0
            
            # 提取所有帧
            while True:
                frame = img.copy()
                if img.tile:
                    frame = frame.resize((580, 580), Image.Resampling.LANCZOS)
                self.gif_frames_result.append(frame)
                try:
                    img.seek(len(self.gif_frames_result))
                except EOFError:
                    break
            
            # 开始动画
            if len(self.gif_frames_result) > 1:
                self.animate_result_gif(top)
            else:
                # 单帧GIF
                photo = ImageTk.PhotoImage(self.gif_frames_result[0])
                label = tk.Label(top, image=photo)
                label.image = photo
                label.pack(pady=10)
        else:
            # 静态图片处理
            img.thumbnail((580, 580), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(top, image=photo)
            label.image = photo
            label.pack(pady=10)
        
        ttk.Button(top, text="保存", command=lambda: self.save_image(image_data)).pack(pady=5)
        top.protocol("WM_DELETE_WINDOW", lambda: self.cleanup_result_gif(top))

    def animate_result_gif(self, window):
        if hasattr(self, 'gif_frames_result') and hasattr(self, 'current_frame_result'):
            frame = self.gif_frames_result[self.current_frame_result]
            photo = ImageTk.PhotoImage(frame)
            
            # 创建或更新标签
            if not hasattr(self, 'result_label'):
                self.result_label = tk.Label(window, image=photo)
                self.result_label.image = photo
                self.result_label.pack(pady=10)
            else:
                self.result_label.config(image=photo)
                self.result_label.image = photo
            
            self.current_frame_result = (self.current_frame_result + 1) % len(self.gif_frames_result)
            delay = frame.info.get('duration', 100)
            window.after(delay, lambda: self.animate_result_gif(window))

    def save_image(self, image_data):
        # 先读取图片数据判断格式
        img = Image.open(BytesIO(image_data))
        format_map = {
            'GIF': '.gif',
            'JPEG': '.jpg',
            'PNG': '.png',
            'WEBP': '.webp'
        }
        default_ext = format_map.get(img.format, '.png')
        
        file = filedialog.asksaveasfilename(
            title="保存表情",
            defaultextension=default_ext,
            filetypes=[
                ("GIF 图片", "*.gif"),
                ("JPEG 图片", "*.jpg"),
                ("PNG 图片", "*.png"),
                ("WEBP 图片", "*.webp"),
                ("所有文件", "*.*")
            ]
        )
        if file:
            # 确保文件名后缀与格式匹配
            ext = os.path.splitext(file)[1].lower()
            if img.format and ext != default_ext.lower():
                # 如果用户选择的后缀不匹配图片格式，提示并自动修正
                if not messagebox.askyesno("格式不匹配", 
                    f"您选择的文件后缀({ext})与图片格式({img.format})不匹配，是否自动修正为{default_ext}？"):
                    return
                file = os.path.splitext(file)[0] + default_ext
            
            with open(file, "wb") as f:
                f.write(image_data)
            messagebox.showinfo("保存成功", f"表情已保存到: {file}")

    # 添加清理方法
    def cleanup_result_gif(self, window):
        if hasattr(self, 'gif_frames_result'):
            del self.gif_frames_result
        if hasattr(self, 'current_frame_result'):
            del self.current_frame_result
        if hasattr(self, 'result_label'):
            del self.result_label
        window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MemeGeneratorApp(root)
    root.mainloop()
