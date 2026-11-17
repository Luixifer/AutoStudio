package com.luixifer.autostudio;

import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;

/** Lists workflow artifacts and securely downloads research-only MP4 previews.
 * GitHub PAT is sent solely to api.github.com; never to redirect hosts.
 */
public final class ResearchArtifactClient {
    public static final String WORKFLOW="investigar-tema.yml";
    public static final String ARTIFACT="AutoStudio-Research-UNREVIEWED-MP4";
    private static final String VIDEO="autostudio-black-hole-REVIEW-ONLY.mp4";
    private static final String REPORT="preview-report.json";
    private static final int MAX_ZIP=26*1024*1024, MAX_VIDEO=20*1024*1024, MAX_REPORT=65536;
    private final String token;
    public ResearchArtifactClient(String token){this.token=token;}

    public static boolean validRunId(String value){return value!=null&&value.matches("[1-9][0-9]{0,19}");}

    private HttpURLConnection apiConnection(String path) throws Exception {
        if(token==null||token.isEmpty())throw new IOException("Conecta GitHub en Ajustes.");
        URL url=new URL("https://api.github.com/repos/"+GitHubClient.REPO+path);
        HttpURLConnection c=(HttpURLConnection)url.openConnection();
        c.setInstanceFollowRedirects(false);
        c.setConnectTimeout(15000);c.setReadTimeout(45000);
        c.setRequestProperty("Authorization","Bearer "+token);
        c.setRequestProperty("Accept","application/vnd.github+json");
        c.setRequestProperty("X-GitHub-Api-Version","2022-11-28");
        c.setRequestProperty("User-Agent","AutoStudio-Research-Lab/0.5");
        return c;
    }
    private static String text(InputStream in,int limit) throws Exception {
        try(InputStream data=in;ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] buffer=new byte[8192];int n;
            while((n=data.read(buffer))!=-1){
                if(out.size()+n>limit)throw new IOException("Respuesta GitHub demasiado grande.");
                out.write(buffer,0,n);
            }
            return out.toString("UTF-8");
        }
    }
    private JSONObject request(String path) throws Exception {
        HttpURLConnection c=apiConnection(path);
        try{
            int status=c.getResponseCode();
            if(status!=200)throw new IOException("GitHub: error "+status+" al consultar los vídeos.");
            return new JSONObject(text(c.getInputStream(),1024*1024));
        }finally{c.disconnect();}
    }
    /** Each list requires two paginated-but-bounded calls, never searches random repositories. */
    public JSONArray researchRuns() throws Exception {
        return request("/actions/workflows/"+WORKFLOW+"/runs?event=workflow_dispatch&per_page=30")
            .getJSONArray("workflow_runs");
    }
    public Map<String,JSONObject> availableVideos() throws Exception {
        JSONArray artifacts=request("/actions/artifacts?per_page=100").getJSONArray("artifacts");
        Map<String,JSONObject> result=new HashMap<>();
        for(int i=0;i<artifacts.length();i++){
            JSONObject a=artifacts.optJSONObject(i);
            if(a==null||!ARTIFACT.equals(a.optString("name"))||a.optBoolean("expired",true))continue;
            JSONObject run=a.optJSONObject("workflow_run");
            if(run==null)continue;
            String runId=run.optString("id");
            if(!validRunId(runId)||!a.optString("id").matches("[1-9][0-9]{0,19}"))continue;
            result.put(runId,a);
        }
        return result;
    }
    public static File localFile(File filesDir,String runId) throws IOException {
        if(!validRunId(runId))throw new IOException("Identificador de ejecución inválido.");
        return new File(new File(filesDir,"research-videos"),runId+".mp4");
    }
    /** GitHub's 302 carries a short-lived URL; never forward the PAT to it. */
    static boolean allowedArchiveHost(URL url) {
        if(!"https".equalsIgnoreCase(url.getProtocol())||url.getPort()!=-1||
           url.getUserInfo()!=null)return false;
        String h=url.getHost().toLowerCase(Locale.ROOT);
        return h.equals("objects.githubusercontent.com")||
               h.equals("results-receiver.actions.githubusercontent.com")||
               (h.endsWith(".blob.core.windows.net") &&
                (h.startsWith("productionresultssa")||h.startsWith("pipelinesghubeus")||
                 h.startsWith("pipelinesghubweu")||h.startsWith("pipelinesghub")));
    }
    private static String readEntry(ZipInputStream zip,int max) throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        byte[] buffer=new byte[8192];int n;
        while((n=zip.read(buffer))!=-1){
            if(out.size()+n>max)throw new IOException("Informe demasiado grande.");
            out.write(buffer,0,n);
        }
        return new String(out.toByteArray(),StandardCharsets.UTF_8);
    }
    private static String digest(File file) throws Exception {
        MessageDigest md=MessageDigest.getInstance("SHA-256");
        try(InputStream stream=new FileInputStream(file)){
            byte[] b=new byte[32768];int n;
            while((n=stream.read(b))!=-1)md.update(b,0,n);
        }
        StringBuilder out=new StringBuilder();
        for(byte b:md.digest())out.append(String.format(Locale.ROOT,"%02x",b&255));
        return out.toString();
    }
    public File download(String runId,JSONObject artifact,File filesDir) throws Exception {
        if(!validRunId(runId)||artifact==null||!ARTIFACT.equals(artifact.optString("name"))||
           artifact.optBoolean("expired",true))throw new IOException("Artefacto de investigación inválido.");
        JSONObject origin=artifact.optJSONObject("workflow_run");
        if(origin==null||!runId.equals(origin.optString("id")))throw new IOException("Vídeo de otra ejecución.");
        String artifactId=artifact.optString("id");
        if(!artifactId.matches("[1-9][0-9]{0,19}"))throw new IOException("Identificador de artefacto inválido.");
        File destination=localFile(filesDir,runId);
        File parent=destination.getParentFile();
        if(!parent.isDirectory()&&!parent.mkdirs())throw new IOException("No se puede crear la carpeta.");
        HttpURLConnection api=apiConnection("/actions/artifacts/"+artifactId+"/zip");
        URL signed;
        try{
            int status=api.getResponseCode();
            if(status!=302&&status!=301)throw new IOException("GitHub no ha autorizado descargar el ZIP: "+status);
            String location=api.getHeaderField("Location");
            if(location==null)throw new IOException("Falta dirección de descarga.");
            signed=new URL(location);
            if(!allowedArchiveHost(signed))throw new IOException("Redirección de GitHub no autorizada.");
        }finally{api.disconnect();}
        HttpURLConnection remote=(HttpURLConnection)signed.openConnection();
        remote.setConnectTimeout(15000);remote.setReadTimeout(60000);
        remote.setInstanceFollowRedirects(false);
        remote.setRequestProperty("User-Agent","AutoStudio-Research-Lab/0.5");
        File tmp=new File(parent,runId+".part");
        if(tmp.exists())tmp.delete();
        boolean hasVideo=false,hasReport=false;
        String reportText=null;
        try{
            if(remote.getResponseCode()!=200)throw new IOException("No se pudo abrir el archivo de GitHub.");
            try(InputStream body=remote.getInputStream();
                ZipInputStream zip=new ZipInputStream(new BufferedInputStream(new FilterInputStream(body){
                    int used=0;
                    @Override public int read() throws IOException {
                        int n=super.read();if(n!=-1&&++used>MAX_ZIP)throw new IOException("ZIP excesivo.");return n;
                    }
                    @Override public int read(byte[] b,int off,int len) throws IOException {
                        int n=super.read(b,off,len);
                        if(n>0&&(used+=n)>MAX_ZIP)throw new IOException("ZIP excesivo.");
                        return n;
                    }
                }))) {
                ZipEntry entry;
                while((entry=zip.getNextEntry())!=null){
                    String name=entry.getName();
                    if(entry.isDirectory())continue;
                    if(VIDEO.equals(name)){
                        if(hasVideo)throw new IOException("MP4 duplicado.");
                        hasVideo=true;
                        try(FileOutputStream output=new FileOutputStream(tmp)){
                            byte[] buffer=new byte[32768];int n;long total=0;
                            while((n=zip.read(buffer))!=-1){
                                total+=n;if(total>MAX_VIDEO)throw new IOException("MP4 demasiado grande.");
                                output.write(buffer,0,n);
                            }
                            output.getFD().sync();
                        }
                    }else if(REPORT.equals(name)){
                        if(hasReport)throw new IOException("Informe duplicado.");
                        hasReport=true;reportText=readEntry(zip,MAX_REPORT);
                    }else{
                        throw new IOException("El ZIP contiene archivos no previstos.");
                    }
                    zip.closeEntry();
                }
            }
            if(!hasVideo||!hasReport||!tmp.isFile()||tmp.length()<10000)
                throw new IOException("Artefacto incompleto.");
            JSONObject report=new JSONObject(reportText);
            String expected=report.optString("sha256");
            if(!"experimental_unapproved_preview".equals(report.optString("status"))||
                report.optBoolean("scientifically_approved",true)||
                report.optBoolean("youtube_enabled",true)||
                !VIDEO.equals(report.optString("video_file"))||
                !expected.matches("[a-f0-9]{64}")||!digest(tmp).equals(expected))
                throw new IOException("El vídeo no coincide con el informe SHA-256 o no está marcado como borrador.");
            if(destination.exists()&&!destination.delete())throw new IOException("No se pudo sustituir la copia.");
            if(!tmp.renameTo(destination))throw new IOException("No se pudo confirmar la descarga.");
            return destination;
        }finally{
            remote.disconnect();
            if(tmp.exists())tmp.delete();
        }
    }
}
