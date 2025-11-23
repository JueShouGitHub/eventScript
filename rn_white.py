#!/usr/bin/env python3
# setup_rn_white_pre_integration.py - 仅执行 RN 白包的预集成阶段（不包含 RN+Dex 集成）
import os
import subprocess
import json
import re
import shutil
import random
import string
from pathlib import Path
from typing import Optional

# =================== 模板代码 ===================

APP_TSX_WHITE = '''/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 *
 * @format
 */

import { StatusBar, StyleSheet } from 'react-native';
import WebView from 'react-native-webview';
import { useEffect, useRef } from 'react';
import Orientation from 'react-native-orientation-locker';
import { SafeAreaView } from 'react-native-safe-area-context';

function App() {
  // @ts-ignore
  const objRef = useRef();

  Orientation.lockToLandscape();

  // useEffect(() => {
  // }, []);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar hidden={true} />
      <WebView
        source={{
          uri: '{GAME_URL}',
        }}
        style={styles.container}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

export default App;
'''

PACKAGE_JSON_DEPENDENCIES = {
    "dependencies": {
        "@react-native/new-app-screen": "0.82.1",
        "axios": "^1.11.0",
        "react": "19.1.1",
        "react-native": "0.82.1",
        "react-native-orientation-locker": "^1.7.0",
        "react-native-safe-area-context": "^5.5.2",
        "react-native-webview": "^13.16.0",
        "react-native-device-info": "^14.0.4",
    }
}

# =================== 预集成阶段函数 ===================

def validate_environment() -> bool:
    """验证必需的工具是否可用"""
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


def validate_inputs(app_name: str, package_name: str) -> bool:
    """验证输入格式"""
    # 验证应用名称格式
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', app_name):
        print("❌ 应用名称格式错误！只能包含字母、数字、下划线和连字符，且必须以字母开头")
        return False

    # 验证包名格式（android 包名必须全部小写）
    if not re.match(r'^[a-z][a-z0-9_]*(\.{1}[a-z][a-z0-9_]*)+$', package_name):
        print("❌ 包名格式错误！请使用标准格式，如 com.company.app")
        return False

    return True


def generate_random_package_name() -> str:
    """生成随机包名，格式：com.xxx.xxx，确保是标准的三层结构"""
    def generate_random_part(max_length: int = 6) -> str:
        length = random.randint(3, max_length)  # 至少3个字符
        first_char = random.choice(string.ascii_lowercase)
        remaining_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length-1))
        return first_char + remaining_chars

    company_name = generate_random_part()
    app_name = generate_random_part()
    package_name = f"com.{company_name}.{app_name}"

    print(f"📦 自动生成包名: {package_name}")
    return package_name


def fix_android_package_structure(package_name: str, app_name: str):
    """修复Android目录中的重复com文件夹问题"""
    # Android Java源码路径
    java_src_path = Path("android/app/src/main/java")
    if not java_src_path.exists():
        print("⚠️  Android源码目录不存在，跳过修复")
        return

    package_parts = package_name.split('.')

    com_dir = java_src_path / "com"
    if not com_dir.exists() or not com_dir.is_dir():
        print("⚠️  Android目录结构异常，跳过修复")
        return

    com_subdirs = [d for d in com_dir.iterdir() if d.is_dir()]
    print(f"🔍 com目录下的子目录: {[d.name for d in com_subdirs]}")

    if len(com_subdirs) == 1:
        subdir_name = com_subdirs[0].name
        print(f"🔍 检查子目录: {subdir_name}")

        # 错误结构: com/com.company.app/
        if '.' in subdir_name and (subdir_name == package_name or package_name.endswith(subdir_name)):
            print(f"🔄 检测到重复com文件夹结构，正在修复...")
            print(f"   错误路径: com/{subdir_name}/")
            print(f"   正确路径应该是: {'/'.join(['com'] + package_parts[1:])}/")

            # 创建正确目录结构
            correct_path = com_dir
            try:
                for part in package_parts[1:]:  # 跳过第一个"com"
                    correct_path = correct_path / part
                    if not correct_path.exists():
                        correct_path.mkdir(parents=True, exist_ok=True)
                        print(f"   创建目录: {correct_path}")
            except Exception as e:
                print(f"❌ 创建目录失败: {e}")
                return

            # 移动文件到正确位置
            wrong_path = com_subdirs[0]
            correct_file_path = correct_path

            try:
                files_moved = 0
                for file in wrong_path.iterdir():
                    if file.is_file():
                        target_file = correct_file_path / file.name
                        print(f"   移动文件: {file.name} -> {target_file}")
                        shutil.move(str(file), str(target_file))
                        files_moved += 1

                print(f"   删除错误目录: {wrong_path}")
                shutil.rmtree(str(wrong_path))

                print(f"✅ Android目录结构修复完成，共移动 {files_moved} 个文件")
            except Exception as e:
                print(f"❌ 移动文件时出错: {e}")
                return
        else:
            print(f"✅ 子目录 {subdir_name} 看起来是正确的")

    print("✅ Android目录结构正常，无需修复")


def add_android_permissions():
    """在AndroidManifest.xml中添加所需权限（遵循编码回退规范）"""
    manifest_path = Path("android/app/src/main/AndroidManifest.xml")

    if not manifest_path.exists():
        print("⚠️  AndroidManifest.xml文件不存在，跳过权限添加")
        return

    permissions = [
        '<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />',
        '<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />',
        '<uses-permission android:name="com.google.android.gms.permission.AD_ID" />',
        '<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />',
        '<uses-permission android:name="android.permission.INTERNET" />'
    ]

    try:
        try:
            content = manifest_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = manifest_path.read_text()

        permissions_added = 0
        for permission in permissions:
            permission_name = permission.split('"')[1]
            if permission_name not in content:
                manifest_pos = content.find('<manifest')
                if manifest_pos != -1:
                    manifest_end_pos = content.find('>', manifest_pos)
                    if manifest_end_pos != -1:
                        insert_pos = manifest_end_pos + 1
                        content = content[:insert_pos] + '\n    ' + permission + content[insert_pos:]
                        permissions_added += 1
                        print(f"✅ 添加权限: {permission_name}")

        if permissions_added > 0:
            try:
                manifest_path.write_text(content, encoding='utf-8')
            except UnicodeEncodeError:
                manifest_path.write_text(content)
            print(f"✅ 成功添加 {permissions_added} 个权限到 AndroidManifest.xml")
        else:
            print("✅ 所需权限已存在，无需重复添加")

    except Exception as e:
        print(f"❌ 添加权限时出错: {e}")


def find_keytool() -> Optional[str]:
    """自动查找keytool命令的路径"""
    if shutil.which('keytool'):
        return 'keytool'

    print("🔍 keytool不在PATH中，正在查找JDK安装路径...")

    common_jdk_paths = []

    if os.name == 'nt':
        java_home = os.environ.get('JAVA_HOME')
        if java_home:
            common_jdk_paths.append(Path(java_home) / 'bin' / 'keytool.exe')

        program_files = ['C:\\Program Files\\Java', 'C:\\Program Files (x86)\\Java']
        for pf in program_files:
            if os.path.exists(pf):
                for jdk_dir in Path(pf).glob('jdk*'):
                    common_jdk_paths.append(jdk_dir / 'bin' / 'keytool.exe')

        android_studio_paths = [
            Path.home() / 'AppData' / 'Local' / 'Android' / 'Sdk' / 'jdk',
            Path('C:\\Program Files\\Android\\Android Studio\\jbr\\bin\\keytool.exe'),
        ]
        for as_path in android_studio_paths:
            if isinstance(as_path, Path):
                if as_path.exists():
                    if as_path.is_file():
                        common_jdk_paths.append(as_path)
                    else:
                        for jdk_dir in as_path.glob('*'):
                            common_jdk_paths.append(jdk_dir / 'bin' / 'keytool.exe')
    else:
        java_home = os.environ.get('JAVA_HOME')
        if java_home:
            common_jdk_paths.append(Path(java_home) / 'bin' / 'keytool')
        common_jdk_paths.extend([
            Path('/usr/bin/keytool'),
            Path('/usr/local/bin/keytool'),
        ])

    for path in common_jdk_paths:
        if path.exists():
            print(f"✅ 找到keytool: {path}")
            return str(path)

    print("❌ 未找到keytool，请确保已安装JDK")
    return None


def generate_jks_file() -> Optional[dict]:
    """生成JKS签名文件并返回签名信息"""
    try:
        keytool_path = find_keytool()
        if not keytool_path:
            print("❌ 无法找到keytool命令")
            print("💡 请安装JDK或设置JAVA_HOME环境变量")
            return None

        jks_filename = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 8))) + '.jks'
        key_alias = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
        store_password = '123456'
        key_password = '123456'

        jks_path = Path("android/app") / jks_filename

        cn = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))
        ou = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))
        o = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))
        l = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))
        st = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))
        c = random.choice(['US', 'CN', 'JP', 'UK', 'DE', 'FR'])

        dname = f"CN={cn}, OU={ou}, O={o}, L={l}, ST={st}, C={c}"
        keytool_cmd = [
            keytool_path,
            '-genkeypair',
            '-v',
            '-keystore', str(jks_path),
            '-alias', key_alias,
            '-keyalg', 'RSA',
            '-keysize', '2048',
            '-validity', '10000',
            '-storepass', store_password,
            '-keypass', key_password,
            '-dname', dname
        ]

        print(f"📝 JKS文件名: {jks_filename}")
        print(f"📝 密钥别名: {key_alias}")
        print(f"📝 密码: {store_password}")

        # Windows下路径包含空格需要特殊处理
        if os.name == 'nt':
            # Windows下使用shell=True并手动拼接命令
            cmd_str = f'"{keytool_path}" -genkeypair -v -keystore "{jks_path}" -alias {key_alias} -keyalg RSA -keysize 2048 -validity 10000 -storepass {store_password} -keypass {key_password} -dname "{dname}"'
            result = subprocess.run(cmd_str, capture_output=True, text=True, shell=True)
        else:
            # Linux/Mac下直接使用列表形式
            result = subprocess.run(keytool_cmd, capture_output=True, text=True, shell=False)

        if result.returncode == 0:
            print(f"✅ JKS签名文件生成成功: {jks_path}")
            return {
                'filename': jks_filename,
                'alias': key_alias,
                'storePassword': store_password,
                'keyPassword': key_password
            }
        else:
            print(f"❌ keytool执行失败: {result.stderr}")
            return None

    except FileNotFoundError:
        print("❌ 找不到keytool命令，请确保JDK已正确安装并添加到PATH")
        return None
    except Exception as e:
        print(f"❌ 生成JKS文件时出错: {e}")
        return None


def configure_signing(jks_info: dict) -> bool:
    """配置签名到build.gradle（强制覆盖原有配置）"""
    gradle_path = Path("android/app/build.gradle")

    if not gradle_path.exists():
        print("⚠️  build.gradle文件不存在，跳过签名配置")
        return False

    try:
        try:
            content = gradle_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = gradle_path.read_text()

        if 'signingConfigs' in content:
            print("🔄 检测到原有签名配置，正在删除...")
            content = remove_signing_configs_block(content)

        signing_config = f'''    signingConfigs {{
        debug {{
            storeFile file('{jks_info["filename"]}')
            storePassword '{jks_info["storePassword"]}'
            keyAlias '{jks_info["alias"]}'
            keyPassword '{jks_info["keyPassword"]}'
        }}
        release {{
            storeFile file('{jks_info["filename"]}')
            storePassword '{jks_info["storePassword"]}'
            keyAlias '{jks_info["alias"]}'
            keyPassword '{jks_info["keyPassword"]}'
        }}
    }}

'''

        android_pos = content.find('android {')
        if android_pos == -1:
            print("❌ 未找到android块，无法配置签名")
            return False

        insert_pos = content.find('\n', android_pos) + 1
        content = content[:insert_pos] + signing_config + content[insert_pos:]

        try:
            gradle_path.write_text(content, encoding='utf-8')
        except UnicodeEncodeError:
            gradle_path.write_text(content)

        print("✅ 签名配置完成（已覆盖原有配置）")
        return True

    except Exception as e:
        print(f"❌ 配置签名时出错: {e}")
        return False


def remove_signing_configs_block(content: str) -> str:
    """删除signingConfigs块"""
    pattern = r'\s*signingConfigs\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*'
    content = re.sub(pattern, '\n', content)
    return content


def add_gradle_dependencies():
    """在build.gradle中添加所需依赖"""
    gradle_path = Path("android/app/build.gradle")

    if not gradle_path.exists():
        print("⚠️  build.gradle文件不存在，跳过依赖添加")
        return

    dependencies = [
        'implementation("androidx.appcompat:appcompat:1.7.1")',
        'implementation("com.google.android.material:material:1.13.0")',
        'implementation("androidx.activity:activity:1.11.0")',
        'implementation("androidx.constraintlayout:constraintlayout:2.2.1")',
        'implementation("com.google.code.gson:gson:2.13.2")',
        'implementation \"com.adjust.sdk:adjust-android:4.35.0\"',
        'implementation("com.android.installreferrer:installreferrer:2.2")',
        'implementation \"com.google.android.gms:play-services-ads-identifier:18.1.0\"',
        'implementation("com.adjust.sdk:adjust-android:4.38.5")'
    ]

    try:
        try:
            content = gradle_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = gradle_path.read_text()

        dependencies_pos = content.find("dependencies")
        if dependencies_pos == -1:
            print("❌ 未找到dependencies块，无法添加依赖")
            return

        open_brace_pos = content.find("{", dependencies_pos)
        if open_brace_pos == -1:
            print("❌ 未找到dependencies块的开始大括号，无法添加依赖")
            return

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
            return

        dependencies_added = []
        for dep in dependencies:
            dep_key = dep.split(' ')[0].replace('implementation', '').replace('(', '').replace(')', '').replace("'", '').replace('"', '').strip()
            if dep_key and dep_key not in content:
                dependencies_added.append(dep)

        if dependencies_added:
            first_dep_pos = content.find("implementation", open_brace_pos)
            if first_dep_pos == -1 or first_dep_pos > close_brace_pos:
                insert_pos = open_brace_pos + 1
            else:
                insert_pos = first_dep_pos

            dependencies_content = "\n    " + "\n    ".join(dependencies_added) + "\n\n"
            updated_content = content[:insert_pos] + dependencies_content + content[insert_pos:]

            try:
                gradle_path.write_text(updated_content, encoding='utf-8')
            except UnicodeEncodeError:
                gradle_path.write_text(updated_content)
            print(f"✅ 成功添加 {len(dependencies_added)} 个依赖到 build.gradle")
            for dep in dependencies_added:
                print(f"   - {dep}")
        else:
            print("✅ 所需依赖已存在，无需重复添加")

    except Exception as e:
        print(f"❌ 添加依赖时出错: {e}")


# =================== 主函数 ===================

def main():
    print("🚀 开始创建 RN 白包（预集成版）")

    if not validate_environment():
        return

    app_name = input("请输入应用名称（项目目录名）: ").strip()
    package_name = generate_random_package_name()

    if not validate_inputs(app_name, package_name):
        return

    game_url = ""
    while not game_url.strip():
        game_url = input("请输入游戏 URL: ").strip()
        if not game_url:
            print("❌ 游戏 URL 不能为空，请重新输入")

    project_path = Path(app_name)
    if project_path.exists():
        print(f"❌ 目录 {app_name} 已存在，请删除或换名")
        return

    print(f"\n🔧 创建 React Native 项目: {app_name}")
    try:
        cmd = f'npx @react-native-community/cli init {app_name} --package-name {package_name}'
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 创建项目失败: {e}")
        return
    except FileNotFoundError:
        print("❌ 找不到 npx 命令，请确保 Node.js 已正确安装并添加到 PATH")
        return

    os.chdir(app_name)

    print("\n📦 安装依赖...")
    with open('package.json', 'r') as f:
        pkg = json.load(f)

    pkg["dependencies"].update(PACKAGE_JSON_DEPENDENCIES["dependencies"])
    with open('package.json', 'w') as f:
        json.dump(pkg, f, indent=2)

    try:
        subprocess.check_call("npm install", shell=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装依赖失败: {e}")
        return

    print("\n📝 生成 App.tsx...")
    code = APP_TSX_WHITE.replace('{GAME_URL}', game_url)
    with open('App.tsx', 'w') as f:
        f.write(code)

    print("\n🔧 检查并修复Android目录结构...")
    fix_android_package_structure(package_name, app_name)

    print("\n🔒 添加Android权限...")
    add_android_permissions()

    print("\n📦 添加Gradle依赖...")
    add_gradle_dependencies()

    print("\n🔐 生成JKS签名文件...")
    jks_info = generate_jks_file()
    if not jks_info:
        print("❌ JKS签名文件生成失败")
        return

    print("\n🔧 配置签名文件...")
    if not configure_signing(jks_info):
        print("❌ 签名配置失败")
        return

    print(f"""
🎉 预集成阶段完成！
📁 进入目录: cd {app_name}
📱 构建命令: npx react-native build-android
💡 下一步：可执行 RN+Dex 集成脚本以完成资源、Activity、插件注册等后续步骤
""")


if __name__ == "__main__":
    main()
