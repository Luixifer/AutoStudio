package com.luixifer.autostudio;
import java.util.*;
/** Paragraph boundaries are authorial data, never inferred from media count. */
public final class DirectorQuickPlan {
 public static List<String> paragraphs(String text){
  if(text==null||text.trim().isEmpty())throw new IllegalArgumentException("Escribe o importa el guion.");
  if(text.length()>100000)throw new IllegalArgumentException("El guion supera el límite; impórtalo por capítulos.");
  List<String> result=new ArrayList<>();
  for(String part:text.replace("\r\n","\n").replace('\r','\n').trim().split("\\n[\\t ]*\\n(?:[\\t ]*\\n)*")){
   String paragraph=part.trim();if(paragraph.isEmpty())continue;
   if(paragraph.matches("(?s)^#{1,6}\\s+[^\\n]+$"))continue; // standalone Markdown chapter heading
   if(paragraph.length()>6000)throw new IllegalArgumentException("Un párrafo supera 6000 caracteres. Divídelo explícitamente.");
   result.add(paragraph);
  }
  if(result.isEmpty())throw new IllegalArgumentException("El guion no contiene párrafos narrables.");
  if(result.size()>720)throw new IllegalArgumentException("Demasiadas escenas; divide el documental.");
  return result;
 }
 public static List<String> split(String text,int images){
  List<String> result=paragraphs(text);
  if(images!=result.size())throw new IllegalArgumentException("Hay "+result.size()+" párrafos y "+images+" recursos. Añade o quita recursos: cada párrafo necesita uno, en el mismo orden.");
  return result;
 }
 public static int imageFor(int scene,int scenes,int images){
  if(scenes!=images||scene<0||scene>=scenes)throw new IllegalArgumentException("La asociación párrafo-recurso no es válida.");return scene;
 }
 private DirectorQuickPlan(){}
}
