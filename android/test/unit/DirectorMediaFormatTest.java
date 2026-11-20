import com.luixifer.autostudio.DirectorMediaFormat;
public final class DirectorMediaFormatTest{
 static void expect(String value,byte[] data){String actual=DirectorMediaFormat.detect(data,data.length);if(value==null?actual!=null:!value.equals(actual))throw new AssertionError("Unexpected format");}
 public static void main(String[] args){expect("jpg",new byte[]{-1,-40,-1});expect("png",new byte[]{-119,80,78,71,13,10,26,10});expect("wav","RIFF1234WAVE".getBytes());expect("webp","RIFF1234WEBP".getBytes());expect("mp4","1234ftypisom".getBytes());expect("mp3","ID3".getBytes());expect("mp3",new byte[]{-1,-5});expect(null,new byte[]{});expect(null,"not an image.jpg".getBytes());expect(null,new byte[]{-1,-15});System.out.println("Director real media signature checks passed: 10");}
}
