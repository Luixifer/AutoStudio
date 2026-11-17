package com.luixifer.autostudio;
import android.app.Application;
public final class AutoStudioApp extends Application {
    public static final java.util.concurrent.ExecutorService IO=java.util.concurrent.Executors.newSingleThreadExecutor();
    private JobController controller;
    @Override public void onCreate(){super.onCreate();controller=new JobController(this);}
    public JobController jobs(){return controller;}
}
