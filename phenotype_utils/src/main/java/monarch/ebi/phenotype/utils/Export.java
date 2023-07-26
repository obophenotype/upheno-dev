package monarch.ebi.phenotype.utils;


import org.apache.commons.io.FileUtils;

import java.io.File;
import java.io.IOException;
import java.util.*;

public class Export {

    public static void writeCSV(List<Map<String,String>> data, File out) {
        Set<String> header = new HashSet<>();
        data.forEach(rec->rec.keySet().forEach(k->header.add(k)));
        List<String> columns = new ArrayList<>(header);
        Collections.sort(columns);
        StringBuilder sb = new StringBuilder();
        String headerString = "";
        for(String c:columns) {
            headerString+=c+",";
        }
        headerString = headerString.replaceAll(",$", "");
        sb.append(headerString);
        sb.append("\n");
        for(Map<String,String> rec:data) {
            String rowString = "";
            for (String col : columns) {
                if (rec.containsKey(col)) {
                    String value = rec.get(col);
                    if(value.contains(",")||value.contains("\n")||value.contains("\r")) {
                        rowString+=("\""+value+"\"");
                    } else {
                        rowString+=(value);
                    }

                }
                rowString+=(",");
            }
            rowString = rowString.replaceAll(",$", "");
            sb.append(rowString);
            sb.append("\n");
        }
        try {
            FileUtils.write(out, sb.toString(),"utf-8");
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}

