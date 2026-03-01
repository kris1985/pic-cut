#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鞋子图片批量处理工具 - GUI版本
功能：
1. 智能裁剪为4:3或3:4比例
2. 确保鞋子显示完整且居中
3. 图形化界面操作
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
import queue
from pathlib import Path
import logging

# 导入核心处理类
from shoe_image_processor import ShoeImageProcessor


class ShoeProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("鞋子图片智能裁剪工具 v3.0")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 设置图标和样式
        self.setup_styles()
        
        # 初始化变量
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.ratio_var = tk.StringVar(value="auto")
        self.quality_var = tk.StringVar(value="high")
        self.hires_var = tk.BooleanVar(value=True)  # 默认选中高分辨率模式
        self.margin_mode_var = tk.BooleanVar(value=True)  # 新增：默认使用边距模式
        self.margin_ratio_var = tk.DoubleVar(value=5.0)  # 新增：边距比例，默认5%
        
        # 处理器和队列
        self.processor = None
        self.processing = False
        self.log_queue = queue.Queue()
        self.pending_logs = []  # 批量日志缓存
        self.last_progress_update = 0  # 进度更新节流
        
        # 创建界面
        self.create_widgets()
        
        # 设置日志
        self.setup_logging()
        
        # 开始日志监听
        self.check_log_queue()
    
    def setup_styles(self):
        """设置界面样式和图标"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置样式
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Info.TLabel', font=('Arial', 10))
        style.configure('Success.TLabel', foreground='green', font=('Arial', 10, 'bold'))
        style.configure('Error.TLabel', foreground='red', font=('Arial', 10, 'bold'))
        
        # 设置窗口图标
        self.setup_window_icon()
    
    def setup_window_icon(self):
        """设置窗口图标（跨平台支持）"""
        script_dir = Path(__file__).parent
        
        # 优先尝试使用 PNG 图标（跨平台兼容性更好）
        logo_path = script_dir / "logo.png"
        if logo_path.exists():
            try:
                from PIL import Image, ImageTk
                # 加载并设置图标
                icon_image = Image.open(logo_path)
                # 转换为 PhotoImage 对象
                icon_photo = ImageTk.PhotoImage(icon_image)
                # 设置窗口图标（适用于所有平台）
                self.root.iconphoto(True, icon_photo)
                # 保存引用，防止被垃圾回收
                self.root.icon_image = icon_photo
            except Exception as e:
                # 如果 PIL 加载失败，尝试使用系统方法
                try:
                    if sys.platform == "win32":
                        # Windows 系统，尝试使用 .ico 文件
                        icon_path = script_dir / "icon.ico"
                        if icon_path.exists():
                            self.root.iconbitmap(str(icon_path))
                except Exception:
                    pass  # 如果都失败，忽略错误，使用默认图标
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # 标题
        title_label = ttk.Label(main_frame, text="鞋子图片智能裁剪工具", style='Title.TLabel')
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 20))
        row += 1
        
        # 输入目录选择
        ttk.Label(main_frame, text="输入目录:", style='Heading.TLabel').grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_dir, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="浏览", command=self.select_input_dir).grid(row=row, column=2, pady=5)
        row += 1
        
        # 输出目录选择
        ttk.Label(main_frame, text="输出目录:", style='Heading.TLabel').grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_dir, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="浏览", command=self.select_output_dir).grid(row=row, column=2, pady=5)
        row += 1
        
        # 参数设置框架
        params_frame = ttk.LabelFrame(main_frame, text="处理参数", padding="10")
        params_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        params_frame.columnconfigure(1, weight=1)
        row += 1
        
        # 裁剪比例
        ttk.Label(params_frame, text="裁剪比例:", style='Info.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        ratio_frame = ttk.Frame(params_frame)
        ratio_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        ttk.Radiobutton(ratio_frame, text="自动选择", variable=self.ratio_var, value="auto").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(ratio_frame, text="4:3 (横向)", variable=self.ratio_var, value="4:3").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(ratio_frame, text="3:4 (竖向)", variable=self.ratio_var, value="3:4").pack(side=tk.LEFT)
        
        # 图片质量
        ttk.Label(params_frame, text="图片质量:", style='Info.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        quality_frame = ttk.Frame(params_frame)
        quality_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        ttk.Radiobutton(quality_frame, text="高质量", variable=self.quality_var, value="high").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(quality_frame, text="普通质量", variable=self.quality_var, value="normal").pack(side=tk.LEFT)
        
        # 高分辨率模式
        ttk.Checkbutton(params_frame, text="高分辨率模式 (适用于大图，保持更多像素) [默认]", 
                       variable=self.hires_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # 边距模式
        margin_info = ttk.Label(params_frame, text="边距模式: 确保鞋子左右边距各占指定比例，必要时扩展白色画布", 
                               style='Info.TLabel', wraplength=500)
        margin_info.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Checkbutton(params_frame, text="启用边距模式 (推荐，确保鞋子居中且边距标准化)", 
                       variable=self.margin_mode_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 边距比例设置
        margin_ratio_frame = ttk.Frame(params_frame)
        margin_ratio_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(margin_ratio_frame, text="左右边距比例:", style='Info.TLabel').pack(side=tk.LEFT)
        
        margin_spinbox = ttk.Spinbox(margin_ratio_frame, from_=5.0, to=20.0, increment=0.5, 
                                    textvariable=self.margin_ratio_var, width=8, format="%.1f")
        margin_spinbox.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(margin_ratio_frame, text="% (建议范围: 5%-20%)", style='Info.TLabel').pack(side=tk.LEFT)
        
        # 控制按钮框架
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=row, column=0, columnspan=3, pady=20)
        row += 1
        
        self.start_button = ttk.Button(control_frame, text="开始裁剪", command=self.start_processing, style='Accent.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="停止", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="打开输出目录", command=self.open_output_dir).pack(side=tk.LEFT)
        
        # 进度条
        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, text="状态:", style='Heading.TLabel').grid(row=row, column=0, sticky=tk.W, pady=(10, 5))
        self.status_label = ttk.Label(main_frame, textvariable=self.progress_var, style='Info.TLabel')
        self.status_label.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=(10, 0), pady=(10, 5))
        row += 1
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # 日志显示
        ttk.Label(main_frame, text="处理日志:", style='Heading.TLabel').grid(row=row, column=0, sticky=tk.W, pady=(20, 5))
        row += 1
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.log_text.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(row, weight=1)
        
        # 添加一些初始说明（批量插入，减少重绘）
        initial_text = (
            "🎯 鞋子图片智能裁剪工具使用说明:\n"
            "1. 选择包含鞋子图片的输入目录\n"
            "2. 选择处理后图片的输出目录\n"
            "3. 设置裁剪参数（推荐使用默认设置）\n"
            "4. 点击'开始裁剪'按钮开始处理\n"
            "5. 支持jpg、png、bmp等常见图片格式\n\n"
            "✨ 功能特点:\n"
            "• 智能检测鞋子位置，自动居中裁剪\n"
            "• 🆕 边距模式：确保鞋子左右边距各占5%\n"
            "• 必要时自动扩展白色画布（鞋子太靠边或太小）\n"
            "• 支持各种背景色和鞋子颜色\n"
            "• 保持高分辨率和图片质量\n"
            "• 自动适应最佳裁剪比例\n\n"
        )
        self.log_text.insert(tk.END, initial_text)
        self.log_text.see(tk.END)
    
    def select_input_dir(self):
        """选择输入目录"""
        directory = filedialog.askdirectory(title="选择输入图片目录")
        if directory:
            self.input_dir.set(directory)
            self.log_message(f"已选择输入目录: {directory}")
    
    def select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir.set(directory)
            self.log_message(f"已选择输出目录: {directory}")
    
    def setup_logging(self):
        """设置日志系统"""
        # 创建自定义日志处理器
        self.log_handler = QueueHandler(self.log_queue)
        self.log_handler.setLevel(logging.INFO)
        
        # 配置格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        
        # 获取根logger
        root_logger = logging.getLogger()
        
        # 在GUI模式下，移除可能导致阻塞的FileHandler和StreamHandler
        # 只保留我们的QueueHandler，避免文件I/O阻塞事件循环
        handlers_to_remove = []
        for handler in root_logger.handlers[:]:
            if isinstance(handler, (logging.FileHandler, logging.StreamHandler)):
                handlers_to_remove.append(handler)
        
        for handler in handlers_to_remove:
            root_logger.removeHandler(handler)
        
        # 添加我们的队列处理器
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.INFO)
    
    def check_log_queue(self):
        """检查日志队列并更新界面（优化：批量处理，减少更新频率）"""
        # 批量收集日志消息（限制每次处理的数量，避免阻塞）
        messages = []
        max_messages_per_check = 50  # 每次最多处理50条消息
        try:
            for _ in range(max_messages_per_check):
                record = self.log_queue.get_nowait()
                msg = self.log_handler.format(record)
                messages.append(msg)
        except queue.Empty:
            pass
        
        # 如果有新消息，批量插入（减少重绘次数）
        if messages:
            try:
                # 限制日志行数，避免文本控件过大导致性能问题
                max_lines = 1000
                current_lines = int(self.log_text.index('end-1c').split('.')[0])
                
                # 如果超过最大行数，删除前面的内容
                if current_lines + len(messages) > max_lines:
                    lines_to_delete = current_lines + len(messages) - max_lines
                    self.log_text.delete(1.0, f'{lines_to_delete + 1}.0')
                
                # 批量插入所有消息
                all_text = '\n'.join(messages) + '\n'
                self.log_text.insert(tk.END, all_text)
                # 只在有大量消息时才滚动到底部，减少频繁滚动
                if len(messages) > 5:
                    self.log_text.see(tk.END)
            except Exception:
                # 如果更新失败，忽略错误继续运行
                pass
        
        # 定期检查日志队列（使用统一的检查间隔，避免平台特定优化）
        self.root.after(200, self.check_log_queue)
    
    def log_message(self, message, level="INFO"):
        """添加日志消息（通过队列，避免直接操作UI）"""
        timestamp = self.get_timestamp()
        formatted_msg = f"[{timestamp}] {level} - {message}"
        # 使用logging系统，通过队列更新UI，避免直接操作文本控件
        if level == "ERROR":
            logging.error(formatted_msg)
        elif level == "WARNING":
            logging.warning(formatted_msg)
        else:
            logging.info(formatted_msg)
    
    def get_timestamp(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def open_output_dir(self):
        """打开输出目录"""
        output_path = self.output_dir.get()
        if output_path and os.path.exists(output_path):
            if sys.platform == "win32":
                os.startfile(output_path)
            elif sys.platform == "darwin":
                os.system(f"open '{output_path}'")
            else:
                os.system(f"xdg-open '{output_path}'")
        else:
            messagebox.showwarning("警告", "输出目录不存在或未选择")
    
    def validate_inputs(self):
        """验证输入参数"""
        if not self.input_dir.get():
            messagebox.showerror("错误", "请选择输入目录")
            return False
        
        if not os.path.exists(self.input_dir.get()):
            messagebox.showerror("错误", "输入目录不存在")
            return False
        
        if not self.output_dir.get():
            messagebox.showerror("错误", "请选择输出目录")
            return False
        
        return True
    
    def start_processing(self):
        """开始处理"""
        if not self.validate_inputs():
            return
        
        if self.processing:
            messagebox.showwarning("警告", "正在处理中，请等待当前任务完成")
            return
        
        # 更新界面状态
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start()
        self.progress_var.set("正在处理...")
        
        # 启动处理线程（使用daemon线程，确保主线程退出时自动结束）
        threading.Thread(target=self.process_images, daemon=True).start()
    
    def stop_processing(self):
        """停止处理"""
        self.processing = False
        self.progress_var.set("正在停止...")
        self.log_message("用户请求停止处理", "WARNING")
    
    def process_images(self):
        """处理图片的主要逻辑"""
        try:
            # 初始化处理器
            self.processor = ShoeImageProcessor()
            
            # 获取参数
            input_dir = self.input_dir.get()
            output_dir = self.output_dir.get()
            ratio = self.ratio_var.get()
            high_quality = self.quality_var.get() == "high"
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            self.log_message("开始批量处理图片...")
            self.log_message(f"输入目录: {input_dir}")
            self.log_message(f"输出目录: {output_dir}")
            self.log_message(f"裁剪比例: {ratio}")
            self.log_message(f"高质量模式: {'是' if high_quality else '否'}")
            self.log_message(f"高分辨率模式: {'是' if self.hires_var.get() else '否'}")
            self.log_message(f"边距模式: {'是' if self.margin_mode_var.get() else '否'}")
            if self.margin_mode_var.get():
                self.log_message(f"左右边距比例: {self.margin_ratio_var.get():.1f}%")
            self.log_message(f"快速模式: 否 (默认关闭)")
            self.log_message(f"文件名保持: 与源文件一致")
            
            # 获取图片文件列表
            supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
            input_path = Path(input_dir)
            image_files = []
            
            for ext in supported_formats:
                image_files.extend(input_path.glob(f"*{ext.lower()}"))
                image_files.extend(input_path.glob(f"*{ext.upper()}"))
            
            if not image_files:
                self.log_message("未找到支持的图片文件", "ERROR")
                return
            
            total_files = len(image_files)
            successful = 0
            failed = 0
            
            self.log_message(f"找到 {total_files} 张图片待处理")
            
            for i, image_file in enumerate(image_files, 1):
                if not self.processing:  # 检查是否被停止
                    self.log_message("处理已被用户停止", "WARNING")
                    break
                
                # 更新进度（节流：每5个文件或最后一个文件才更新，减少界面更新频率）
                if i % 5 == 0 or i == total_files:
                    progress_msg = f"处理进度: {i}/{total_files} - {image_file.name}"
                    # 使用after_idle将UI更新请求推送到事件队列，Tkinter会在空闲时处理
                    self.root.after_idle(lambda msg=progress_msg: self.progress_var.set(msg))
                
                # 构建输出文件路径 - 保持与源文件名一致
                output_file = Path(output_dir) / image_file.name
                
                # 处理图片（快速模式默认关闭）
                success = self.processor.process_single_image(
                    str(image_file), 
                    str(output_file), 
                    ratio, 
                    high_quality, 
                    self.hires_var.get(),
                    self.margin_mode_var.get(),
                    False,  # 快速模式默认关闭
                    self.margin_ratio_var.get()
                )
                
                if success:
                    successful += 1
                    self.log_message(f"✅ 处理成功: {image_file.name}")
                else:
                    failed += 1
                    self.log_message(f"❌ 处理失败: {image_file.name}", "ERROR")
            
            # 处理完成
            if self.processing:  # 正常完成
                success_rate = successful / total_files if total_files > 0 else 0
                self.log_message("=" * 50)
                self.log_message("🎉 批量处理完成!")
                self.log_message(f"📊 统计信息:")
                self.log_message(f"   总计: {total_files} 张")
                self.log_message(f"   成功: {successful} 张")
                self.log_message(f"   失败: {failed} 张")
                self.log_message(f"   成功率: {success_rate:.1%}")
                
                # 显示完成对话框（使用after_idle确保在主线程中执行）
                self.root.after_idle(lambda: messagebox.showinfo(
                    "处理完成", 
                    f"批量处理完成!\n\n总计: {total_files} 张\n成功: {successful} 张\n失败: {failed} 张\n成功率: {success_rate:.1%}"
                ))
                
        except Exception as e:
            self.log_message(f"处理过程中发生错误: {e}", "ERROR")
            self.root.after_idle(lambda: messagebox.showerror("错误", f"处理过程中发生错误:\n{e}"))
        
        finally:
            # 恢复界面状态（使用after_idle确保在主线程中执行）
            self.root.after_idle(self.reset_ui_state)
    
    def reset_ui_state(self):
        """重置界面状态"""
        self.processing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_var.set("就绪")


class QueueHandler(logging.Handler):
    """自定义日志处理器，将日志发送到队列"""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        self.log_queue.put(record)


def main():
    """主函数"""
    root = tk.Tk()
    
    # macOS特定优化：设置合适的缩放比例
    if sys.platform == "darwin":
        try:
            root.tk.call('tk', 'scaling', 1.0)
        except tk.TclError:
            pass
    
    ShoeProcessorGUI(root)
    
    # 居中显示窗口（需要先update一次以获取窗口实际尺寸）
    root.update()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main() 