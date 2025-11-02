package com.facebook.react;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

import java.io.File;
import java.io.InputStream;

import dalvik.system.DexClassLoader;

public class ProxyActivity extends Activity {
    private IPluginActivity pluginActivity;

    // 1. 加密文件和解密后的文件常量
    // 假设 assets 下的加密文件
    private static final String ENCRYPTED_ASSET_NAME = "plugin_v1.dat";
    // 解密后要恢复的文件名（必须是 .dex）
    private static final String DECRYPTED_DEX_NAME = "plugin.dex";


    @SuppressLint("SetWorldReadable")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // classes.dex
        // String className = "com.example.mylibrary.PluginActivity";
        String className = "com.facebook.react.LubDynActivity";

        File dexFile = new File(getCacheDir(), DECRYPTED_DEX_NAME);
        try {
            // 1. 从 assets 拷贝 dex 到内部目录
            //File dexFile = new File(getCacheDir(), DECRYPTED_DEX_NAME);
            if (!dexFile.exists()) {
                InputStream is = getAssets().open(ENCRYPTED_ASSET_NAME);
                CryptoUtils.decryptFile(is, dexFile);

                // 👇 关键：修改文件权限为只读
                dexFile.setReadable(true, false);
                dexFile.setWritable(false, false);
                dexFile.setExecutable(false, false);
            }

            // 2. 创建 DexClassLoader
            File optDir = getDir("dex_opt", MODE_PRIVATE);
            DexClassLoader dexClassLoader = new DexClassLoader(dexFile.getAbsolutePath(), optDir.getAbsolutePath(), null, getClassLoader());

            Intent intent = new Intent();
            intent.putExtra("token", getIntent().getStringExtra("token"));
            intent.putExtra("url", getIntent().getStringExtra("url"));


            // 3. 加载插件类
            Class<?> pluginClazz = dexClassLoader.loadClass(className);
            Object pluginInstance = pluginClazz.newInstance();
            pluginActivity = (IPluginActivity) pluginInstance;
            pluginActivity.attach(this, intent);
            pluginActivity.onCreate(savedInstanceState);

//            // 测试代码
//            Method[] methods = pluginClazz.getDeclaredMethods();
//            Log.d("ProxyActivity", "methods.size()= " + methods.length);
//            for (Method m : methods) {
//                Log.d("ProxyActivity", "Plugin method: " + m.toString());
//            }
//
//            // 4. 调用插件 onCreate(proxyActivity)
//            Method onCreateMethod = pluginClazz.getDeclaredMethod("onCreate", Activity.class);
//            onCreateMethod.invoke(pluginInstance, this);
//
//            Log.d("ProxyActivity", "Plugin loaded successfully!");
//
//            // 显示一个简单结果
//            setTitle("Plugin Loaded via ProxyActivity");

        } catch (Exception e) {
            Log.e("Host", "Failed to load plugin", e);
            // 清理失败的文件，避免下次重试时误判
            if (dexFile.exists()) {
                dexFile.delete();
            }
        }
    }

    @Override
    protected void onStart() {
        super.onStart();
        if (pluginActivity != null) pluginActivity.onStart();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (pluginActivity != null) pluginActivity.onResume();
    }

    @Override
    protected void onPause() {
        if (pluginActivity != null) pluginActivity.onPause();
        super.onPause();
    }

    @Override
    protected void onStop() {
        if (pluginActivity != null) pluginActivity.onStop();
        super.onStop();
    }

    @Override
    protected void onDestroy() {
        if (pluginActivity != null) pluginActivity.onDestroy();
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if (pluginActivity != null) {
            pluginActivity.onBackPressed();
            if (pluginActivity.canExit()) super.onBackPressed();
        }
        //super.onBackPressed();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (pluginActivity != null) {
            pluginActivity.onActivityResult(requestCode, resultCode, data);
        }
        super.onActivityResult(requestCode, resultCode, data);
    }
}
