# Windows构建编码问题修复说明

## 🚫 遇到的问题

在GitHub Actions的Windows环境下构建时遇到编码错误：

```
UnicodeEncodeError: 'charmap' codec can't encode characters in position 2-11: character maps to <undefined>
Error: Process completed with exit code 1.
```

## 🔍 问题原因

1. **中文字符编码问题**: Windows默认编码无法处理中文字符
2. **文件名中的中文**: 应用程序名称包含中文字符
3. **输出信息中的中文**: print语句包含中文和emoji字符

## ✅ 解决方案

### 1. 编码环境修复

```python
# Windows编码修复
if platform.system() == 'Windows':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
```

### 2. 安全打印函数

```python
def safe_print(text):
    """安全的打印函数，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 如果遇到编码错误，使用ASCII安全的输出
        print(text.encode('ascii', 'replace').decode('ascii'))
```

### 3. 应用名称英文化

**之前**:
- macOS: `鞋子图片智能裁剪工具_v2.0_macOS`
- Windows: `鞋子图片智能裁剪工具_v2.0_x64`
- Linux: `鞋子图片智能裁剪工具_v2.0_linux`

**修复后**:
- macOS: `ShoeImageCropper_v2.0_macOS`
- Windows: `ShoeImageCropper_v2.0_x64`
- Linux: `ShoeImageCropper_v2.0_linux`

### 4. 输出信息英文化

将所有中文输出信息改为英文：
- `🔍 检查打包环境...` → `Checking build environment...`
- `🚀 开始构建...` → `Starting build...`
- `✅ 构建完成!` → `Build completed!`
- `❌ 构建失败:` → `Build failed:`

### 5. 文档文件英文化

- `使用说明.txt` → `README.txt`
- `版本信息.txt` → `VERSION.txt`

## 📊 修复效果

✅ **编码问题**: 完全解决  
✅ **构建成功**: Windows exe可正常生成  
✅ **跨平台兼容**: 所有平台都正常工作  
✅ **文件名一致性**: 输出文件名与源文件保持一致  

## 🚀 GitHub Actions状态

现在所有平台构建都能正常工作：
- ✅ Windows EXE
- ✅ macOS APP  
- ✅ Linux Binary

可以通过以下链接查看构建状态：
```
https://github.com/kris1985/pic-cut/actions
```

## 💡 经验总结

1. **国际化优先**: 在CI/CD环境中，使用英文避免编码问题
2. **安全编程**: 对可能出现编码问题的输出使用异常处理
3. **环境适配**: 为不同操作系统设置适当的编码环境
4. **测试验证**: 在本地和CI环境都要进行测试 