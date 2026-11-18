package com.luixifer.autostudio;

import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;

/** Personal catalogue media with GitHub provenance and verified SHA-256.
 * Never forwards the GitHub PAT to the signed archive URL.
 * The video is kept even if the Actions artifact expires.
 */
public final class CatalogVideoClient {
    public static final String WORKFLOW="personal-topic.yml";
    private static final String VIDEO="render/autostudio-personal-REVIEW.mp4";
    private static final String REPORT="render/quality-report.json";
    private static final long MAX_ARCHIVE=40L*1024*1024;
    private static final long MAX_VIDEO=32L*1024*1024;
    private final String token;
    public CatalogVideoClient(String token){this.token=token;}

    public static boolean validTheme(String v){
        return "auroras".equals(v)||"dna".equals(v)||"volcanoes".equals(v);
    }
    public static boolean validRunId(String v){return ResearchArtifactClient.validRunId(v);}
    public static String themeFor(String artifact){
        if(artifact==null)return null;
        for(String key:new String[]{"auroras","dna","volcanoes"})
            if(artifact.equals("AutoStudio-Personal-"+key+"-Alex-REVIEW"))return key;
        if(artifact.matches("AutoStudio-Custom-[a-f0-9]{32}-Alex-REVIEW"))return "personalizado";
        return null;
    }
    static File local(File filesDir,String run) throws IOException {
        if(!validRunId(run))throw new IOException("Ejecución inválida.");
        return new File(new File(filesDir,"personal-videos"),run+".mp4");
    }
    private HttpURLConnection api(String endpoint) throws IOException {
        if(token==null||token.trim().isEmpty())throw new IOException("Conecta GitHub en Ajustes.");
        URL url=new URL("https://api.github.com/repos/"+GitHubClient.REPO+endpoint);
        HttpURLConnection c=(HttpURLConnection)url.openConnection();
        c.setInstanceFollowRedirects(false);
        c.setConnectTimeout(15000);
        c.setReadTimeout(45000);
        c.setRequestProperty("Authorization","Bearer "+token);
        c.setRequestProperty("Accept","application/vnd.github+json");
        c.setRequestProperty("User-Agent","AutoStudio-Personal-Lab-0.6");
        c.setRequestProperty("X-GitHub-Api-Version","2022-11-28");
        return c;
    }
    private static byte[] limit(InputStream stream,long cap) throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        byte[] b=new byte[16384];int count;
        while((count=stream.read(b))!=-1){
            if(out.size()+count>cap)throw new IOException("Archivo demasiado grande.");
            out.write(b,0,count);
        }
        return out.toByteArray();
    }
    private JSONObject get(String path) throws Exception {
        HttpURLConnection c=api(path);
        try {
            int status=c.getResponseCode();
            if(status!=200)throw new IOException("GitHub rechazó la consulta: HTTP "+status);
            return new JSONObject(new String(limit(c.getInputStream(),1024*1024),StandardCharsets.UTF_8));
        }finally {c.disconnect();}
    }
    public JSONArray runs() throws Exception {
        return get("/actions/workflows/"+WORKFLOW+"/runs?event=workflow_dispatch&per_page=30")
            .getJSONArray("workflow_runs");
    }
    public JSONArray customRuns() throws Exception {
        return get("/actions/workflows/personal-custom.yml/runs?event=workflow_dispatch&per_page=30")
            .getJSONArray("workflow_runs");
    }
    public Map<String,JSONObject> videos() throws Exception {
        JSONArray list=get("/actions/artifacts?per_page=100").getJSONArray("artifacts");
        Map<String,JSONObject> results=new HashMap<>();
        for(int i=0;i<list.length();i++){
            JSONObject artifact=list.optJSONObject(i);
            if(artifact==null||artifact.optBoolean("expired",true)||
               themeFor(artifact.optString("name"))==null)continue;
            JSONObject run=artifact.optJSONObject("workflow_run");
            if(run==null)continue;
            String id=run.optString("id");
            if(!validRunId(id)||!artifact.optString("id").matches("[1-9][0-9]{0,19}"))continue;
            results.put(id,artifact);
        }
        return results;
    }
    public File download(String runId,JSONObject artifact,File root) throws Exception {
        if(!validRunId(runId)||artifact==null||artifact.optBoolean("expired",true)||
           themeFor(artifact.optString("name"))==null)
            throw new IOException("Este vídeo no procede del catálogo personal.");
        JSONObject provenance=artifact.optJSONObject("workflow_run");
        if(provenance==null||!runId.equals(provenance.optString("id")))
            throw new IOException("La ejecución y el vídeo no coinciden.");
        String artifactId=artifact.optString("id");
        if(!artifactId.matches("[1-9][0-9]{0,19}"))throw new IOException("Identificador de artefacto inválido.");
        File destination=local(root,runId);
        if(!destination.getParentFile().isDirectory()&&!destination.getParentFile().mkdirs())
            throw new IOException("No se puede crear la biblioteca.");
        HttpURLConnection request=api("/actions/artifacts/"+artifactId+"/zip");
        URL signed;
        try{
            int status=request.getResponseCode();
            if(status!=302&&status!=301)throw new IOException("GitHub no permite descargar el ZIP: "+status);
            String location=request.getHeaderField("Location");
            if(location==null)throw new IOException("GitHub no devolvió archivo.");
            signed=new URL(location);
            if(!ResearchArtifactClient.allowedArchiveHost(signed))
                throw new IOException("URL de descarga no autorizada.");
        }finally{request.disconnect();}
        HttpURLConnection remote=(HttpURLConnection)signed.openConnection();
        remote.setInstanceFollowRedirects(false);
        remote.setConnectTimeout(15000);remote.setReadTimeout(60000);
        remote.setRequestProperty("User-Agent","AutoStudio-Personal-Lab-0.6");
        File tmp=new File(destination.getParentFile(),runId+".part");
        if(tmp.exists())tmp.delete();
        String report=null;
        boolean video=false;
        try{
            if(remote.getResponseCode()!=200)throw new IOException("No se pudo recuperar el ZIP.");
            try(InputStream original=remote.getInputStream();
                InputStream bounded=new FilterInputStream(original){
                    long consumed=0;
                    private void count(int n)throws IOException {
                        if(n>0&&(consumed+=n)>MAX_ARCHIVE)throw new IOException("ZIP demasiado grande.");
                    }
                    @Override public int read()throws IOException{
                        int n=super.read();if(n!=-1)count(1);return n;
                    }
                    @Override public int read(byte[] b,int o,int l)throws IOException{
                        int n=super.read(b,o,l);count(n);return n;
                    }
                };
                ZipInputStream zip=new ZipInputStream(new BufferedInputStream(bounded))){
                ZipEntry e;int entries=0;
                while((e=zip.getNextEntry())!=null){
                    if(++entries>20)throw new IOException("Demasiados archivos.");
                    if(e.isDirectory())continue;
                    String name=e.getName();
                    if(VIDEO.equals(name)){
                        if(video)throw new IOException("MP4 repetido.");
                        video=true;
                        long total=0;
                        try(FileOutputStream out=new FileOutputStream(tmp)){
                            byte[] b=new byte[32768];int n;
                            while((n=zip.read(b))!=-1){
                                if((total+=n)>MAX_VIDEO)throw new IOException("MP4 excesivo.");
                                out.write(b,0,n);
                            }
                            out.getFD().sync();
                        }
                    }else if(REPORT.equals(name)){
                        if(report!=null)throw new IOException("Informe duplicado.");
                        report=new String(limit(zip,128*1024),StandardCharsets.UTF_8);
                    }else if(name.equals("render/visual-audit.json")||
                            name.equals("render/contacto-planos.jpg")||
                            name.equals("render/captions.srt")||
                            name.equals("storyboard/storyboard.json")){
                        limit(zip,2*1024*1024);
                    }else{
                        throw new IOException("Archivo inesperado en el vídeo.");
                    }
                    zip.closeEntry();
                }
            }
            if(!video||report==null||!tmp.isFile()||tmp.length()<10000)
                throw new IOException("Vídeo o informe ausentes.");
            JSONObject info=new JSONObject(report);
            if(!info.optBoolean("technical_passed",false)||
               info.optBoolean("ready_to_publish",true)||
               info.optBoolean("youtube_enabled",true)||
               info.optJSONArray("shots")==null||
               info.optJSONArray("shots").length()!=8||
               !info.has("visual_audit")||
               info.getJSONObject("visual_audit").optInt("shots_checked")!=8)
                throw new IOException("El vídeo no supera el control de calidad experimental.");
            String sha=info.optString("sha256");
            if(!sha.matches("[a-f0-9]{64}")||!sha.equals(GitHubClient.sha256(tmp)))
                throw new IOException("El MP4 no coincide con su SHA-256.");
            if(destination.exists()&&!destination.delete())throw new IOException("No se pudo sustituir la caché.");
            if(!tmp.renameTo(destination))throw new IOException("No se pudo guardar el MP4.");
            return destination;
        }finally{
            remote.disconnect();
            if(tmp.exists())tmp.delete();
        }
    }
}
