package com.luixifer.autostudio;
/** Magic bytes, not a filename or a provider's optional MIME metadata. */
public final class DirectorMediaFormat {
 public static String detect(byte[] h,int n){
  if(n>=3&&(h[0]&255)==255&&(h[1]&255)==216&&(h[2]&255)==255)return "jpg";
  if(n>=8&&(h[0]&255)==137&&h[1]==80&&h[2]==78&&h[3]==71&&h[4]==13&&h[5]==10&&h[6]==26&&h[7]==10)return "png";
  if(n>=12&&h[0]=='R'&&h[1]=='I'&&h[2]=='F'&&h[3]=='F'){
   if(h[8]=='W'&&h[9]=='E'&&h[10]=='B'&&h[11]=='P')return "webp";
   if(h[8]=='W'&&h[9]=='A'&&h[10]=='V'&&h[11]=='E')return "wav";
  }
  if(n>=12&&h[4]=='f'&&h[5]=='t'&&h[6]=='y'&&h[7]=='p')return "mp4";
  if(n>=3&&h[0]=='I'&&h[1]=='D'&&h[2]=='3')return "mp3";
  if(n>=2&&(h[0]&255)==255&&(h[1]&224)==224&&(h[1]&6)==2)return "mp3";
  return null;
 }
 private DirectorMediaFormat(){}
}
