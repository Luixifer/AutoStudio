package com.luixifer.autostudio;
import android.content.Context;
import org.json.*;
import java.io.*;
import java.util.*;
/** Bundled snapshot from the published server catalog; never advertises free-topic AI. */
public final class TopicCatalog {
    public static final class Topic {
        public final String id,name;
        Topic(String i,String n){id=i;name=n;}
        @Override public String toString(){return name;}
    }
    public static List<Topic> load(Context context) throws Exception {
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();try(InputStream in=context.getAssets().open("catalog.json")){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(bytes.size()+n>128*1024)throw new IOException("Catálogo demasiado grande.");bytes.write(b,0,n);}}
        JSONObject data=new JSONObject(bytes.toString("UTF-8"));JSONArray entries=data.getJSONArray("topics");List<Topic> result=new ArrayList<>();Set<String> seen=new HashSet<>();
        for(int i=0;i<entries.length();i++){JSONObject entry=entries.getJSONObject(i);if(!entry.optBoolean("published",true))continue;String id=entry.getString("id"),name=entry.getString("name");if(!id.matches("[a-z][a-z0-9-]{1,39}")||name.length()>160||!seen.add(id))throw new IOException("Catálogo inválido.");result.add(new Topic(id,name));}
        if(result.isEmpty())throw new IOException("No hay temas publicados.");return result;
    }
    private TopicCatalog(){}
}
