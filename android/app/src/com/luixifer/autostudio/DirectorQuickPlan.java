package com.luixifer.autostudio;
import java.util.*;

/** Pure editorial grouping; never estimates audio duration or changes the script. */
public final class DirectorQuickPlan {
 public static List<String> split(String text,int images){
  if(images<1||images>30)throw new IllegalArgumentException("Selecciona entre 1 y 30 imágenes.");
  String clean=text.trim();if(clean.isEmpty())throw new IllegalArgumentException("Pega el texto que quieres narrar.");
  if(clean.length()>100000)throw new IllegalArgumentException("El texto es demasiado largo; divide el proyecto.");
  String[] words=clean.split("\\s+");
  if(images>words.length)throw new IllegalArgumentException("El texto es demasiado breve para tantas imágenes. Añade texto o quita alguna imagen.");
  int count=Math.max(images,(words.length+99)/100);
  List<String> result=new ArrayList<>();int start=0;
  for(int i=0;i<count;i++){
   int remaining=count-i,end=start+(words.length-start+remaining-1)/remaining;
   // Prefer a nearby sentence boundary, while reserving words for every scene.
   if(remaining>1){int limit=Math.min(words.length-(remaining-1),end+12);for(int k=end;k<=limit;k++)if(words[k-1].matches(".*[.!?][\"»)]?$")){end=k;break;}}
   String part=String.join(" ",Arrays.copyOfRange(words,start,end));
   if(part.length()>6000)throw new IllegalArgumentException("Hay un fragmento demasiado largo para narrarlo.");
   result.add(part);start=end;
  }
  return result;
 }
 public static int imageFor(int scene,int scenes,int images){return Math.min(images-1,(int)((long)scene*images/scenes));}
 private DirectorQuickPlan(){}
}
