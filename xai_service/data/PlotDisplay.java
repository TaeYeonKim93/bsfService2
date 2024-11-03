import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import javax.imageio.ImageIO;
import javax.swing.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;

public class PlotDisplay {

    private static final String SERVER_URL = "http://localhost:5000/generate_plot";

    public static void main(String[] args) {
        String sido = "경상남도";
        String sigungu = "고성군";

        BufferedImage image = fetchPlotImage(sido, sigungu);
        if (image != null) {
            displayImage(image);
        } else {
            System.out.println("이미지를 가져오지 못했습니다.");
        }
    }

    // Flask 서버에서 이미지를 가져오는 메서드
    private static BufferedImage fetchPlotImage(String sido, String sigungu) {
        try {
            // 서버 URL 설정
            URL url = new URL(SERVER_URL);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json; utf-8");
            conn.setRequestProperty("Accept", "application/json");
            conn.setDoOutput(true);

            // JSON 요청 데이터 생성 (ObjectMapper 대신 수동으로 작성)
            String jsonInputString = String.format("{\"sido\": \"%s\", \"sigungu\": \"%s\"}", sido, sigungu);

            // 요청 본문에 JSON 데이터 추가
            try (OutputStream os = conn.getOutputStream()) {
                byte[] input = jsonInputString.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }

            // 응답 코드 확인
            int responseCode = conn.getResponseCode();
            System.out.println("Response Code: " + responseCode);

            if (responseCode == HttpURLConnection.HTTP_OK) {
                // 성공적인 응답을 BufferedReader로 읽어들임
                try (BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                    StringBuilder response = new StringBuilder();
                    String responseLine;
                    while ((responseLine = br.readLine()) != null) {
                        response.append(responseLine.trim());
                    }

                    // JSON 응답 파싱 (ObjectMapper 대신 수동으로 처리)
                    String jsonResponse = response.toString();
                    if (jsonResponse.contains("\"success\":true")) {
                        // Base64 이미지 추출
                        int startIndex = jsonResponse.indexOf("\"image\":\"") + 9;
                        int endIndex = jsonResponse.indexOf("\"", startIndex);
                        String base64Image = jsonResponse.substring(startIndex, endIndex);

                        // Base64 이미지 디코딩하여 BufferedImage로 변환
                        byte[] imageBytes = Base64.getDecoder().decode(base64Image);
                        return ImageIO.read(new ByteArrayInputStream(imageBytes));
                    } else {
                        int messageStart = jsonResponse.indexOf("\"message\":\"") + 11;
                        int messageEnd = jsonResponse.indexOf("\"", messageStart);
                        String errorMessage = jsonResponse.substring(messageStart, messageEnd);
                        System.out.println("서버에서 오류 발생: " + errorMessage);
                    }
                }
            } else {
                // 에러 응답 읽기
                try (BufferedReader br = new BufferedReader(new InputStreamReader(conn.getErrorStream(), StandardCharsets.UTF_8))) {
                    StringBuilder errorResponse = new StringBuilder();
                    String responseLine;
                    while ((responseLine = br.readLine()) != null) {
                        errorResponse.append(responseLine.trim());
                    }
                    System.out.println("Error response: " + errorResponse.toString());
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    // 이미지를 GUI로 표시하는 메서드
    private static void displayImage(BufferedImage image) {
        JFrame frame = new JFrame("Generated Plot");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(800, 600);

        JLabel label = new JLabel(new ImageIcon(image));
        frame.getContentPane().add(label, BorderLayout.CENTER);

        frame.pack();
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }
}
