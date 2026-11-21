import com.luixifer.autostudio.DirectorQuickPlan;
import java.util.*;
public final class DirectorQuickPlanTest {
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args){
  String first=String.join(" ",Collections.nCopies(301,"palabra"));String text=first+"\n\nSegunda escena.\n\nTercera escena.";
  List<String> scenes=DirectorQuickPlan.split(text,3);check(scenes.size()==3);check(scenes.get(0).equals(first));check(scenes.get(1).equals("Segunda escena."));
  for(int i=0;i<3;i++)check(DirectorQuickPlan.imageFor(i,3,3)==i);
  for(int n:new int[]{0,1,2,4}){try{DirectorQuickPlan.split(text,n);throw new AssertionError();}catch(IllegalArgumentException expected){}}
  check(DirectorQuickPlan.paragraphs("# Capítulo\r\n\r\nUno.\r\n \r\nDos.").size()==2);
  check(DirectorQuickPlan.paragraphs("Una línea\ncontinúa el mismo párrafo.").size()==1);
  try{DirectorQuickPlan.imageFor(0,3,2);throw new AssertionError();}catch(IllegalArgumentException expected){}
  System.out.println("Strict paragraph plan: 1:1 identity, mismatch blocked, no word splitting/reuse PASS");
 }
}
