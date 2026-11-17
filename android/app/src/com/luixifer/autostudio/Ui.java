package com.luixifer.autostudio;
import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.view.*;
import android.widget.*;

public final class Ui {
    public static final int INK=Color.rgb(22,38,57),MUTED=Color.rgb(78,96,115),BG=Color.rgb(243,246,250),ACCENT=Color.rgb(8,127,120);
    public static final int TOPIC=1001,GENERATE=1002,STATUS=1003,PLAY=1004,SETTINGS=1005,TOKEN=1006,CONNECT=1007,CONNECTION=1008,SCENES=1009;
    public static int dp(Context c,float n){return (int)(c.getResources().getDisplayMetrics().density*n+.5f);}
    public static LinearLayout root(Activity a,String title){
        a.getWindow().setStatusBarColor(BG);a.getWindow().setNavigationBarColor(BG);
        LinearLayout frame=new LinearLayout(a);frame.setOrientation(1);frame.setBackgroundColor(BG);
        frame.setOnApplyWindowInsetsListener((v,insets)->{if(Build.VERSION.SDK_INT>=30){android.graphics.Insets i=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());v.setPadding(i.left,i.top,i.right,i.bottom);}else v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());return insets;});
        a.setContentView(frame);frame.requestApplyInsets();
        TextView heading=text(a,title,25,true);heading.setPadding(dp(a,22),dp(a,18),dp(a,22),dp(a,14));frame.addView(heading);return frame;
    }
    public static LinearLayout scroll(Activity a,LinearLayout frame){ScrollView s=new ScrollView(a);s.setFillViewport(true);frame.addView(s,new LinearLayout.LayoutParams(-1,0,1));LinearLayout body=new LinearLayout(a);body.setOrientation(1);body.setPadding(dp(a,20),dp(a,6),dp(a,20),dp(a,24));s.addView(body);return body;}
    public static TextView text(Context c,String value,int sp,boolean bold){TextView t=new TextView(c);t.setText(value);t.setTextSize(sp);t.setTextColor(INK);t.setLineSpacing(dp(c,3),1);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
    public static TextView para(LinearLayout p,String value){TextView t=text(p.getContext(),value,15,false);t.setTextColor(MUTED);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,0,0,dp(p.getContext(),14));p.addView(t,lp);return t;}
    public static LinearLayout card(LinearLayout p){Context c=p.getContext();LinearLayout b=new LinearLayout(c);b.setOrientation(1);b.setPadding(dp(c,17),dp(c,17),dp(c,17),dp(c,17));GradientDrawable d=new GradientDrawable();d.setColor(Color.WHITE);d.setCornerRadius(dp(c,18));d.setStroke(dp(c,1),0xffe0e8ee);b.setBackground(d);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,0,0,dp(c,16));p.addView(b,lp);return b;}
    public static Button button(LinearLayout p,String label,int id,boolean main){Context c=p.getContext();Button b=new Button(c);b.setId(id);b.setText(label);b.setAllCaps(false);b.setTextSize(16);b.setMinHeight(dp(c,52));b.setTextColor(main?Color.WHITE:ACCENT);GradientDrawable d=new GradientDrawable();d.setColor(main?ACCENT:0xffe4f3f1);d.setCornerRadius(dp(c,13));b.setBackground(d);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(c,7),0,dp(c,7));p.addView(b,lp);return b;}
    public static void error(Activity a,String message){new AlertDialog.Builder(a).setTitle("No se ha completado").setMessage(message).setPositiveButton("Entendido",null).show();}
    public static void browser(Activity a,String url){try{a.startActivity(new Intent(Intent.ACTION_VIEW,android.net.Uri.parse(url)));}catch(ActivityNotFoundException e){error(a,"No se encontró un navegador.");}}
    private Ui(){}
}
