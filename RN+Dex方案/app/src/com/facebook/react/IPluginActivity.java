package com.facebook.react;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

import androidx.annotation.Nullable;

public interface IPluginActivity {
    void attach(Activity proxyActivity, Intent intent);  // 绑定宿主的代理Activity

    void onCreate(Bundle savedInstanceState);

    void onStart();

    void onResume();

    void onPause();

    void onStop();

    void onDestroy();

    void onBackPressed();

    boolean canExit();

    void onActivityResult(int requestCode, int resultCode, @Nullable Intent data);
}
