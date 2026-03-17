import javafx.application.Application;
import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.ProgressIndicator;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.VBox;
import javafx.stage.FileChooser;
import javafx.stage.Stage;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.util.concurrent.CompletableFuture;

public class ArtForgeryDetectionApp extends Application {

    private File selectedFile;
    private ImageView imagePreview;
    private Button analyzeButton;
    private ProgressIndicator loadingSpinner;
    private Label statusLabel;
    private Label scoreLabel;

    private static final HttpClient httpClient = HttpClient.newHttpClient();
    private static final String SERVER_URL = "http://localhost:5000/analyze";

    @Override
    public void start(Stage primaryStage) {
        primaryStage.setTitle("Art Forgery Detection Engine");

        
        VBox root = new VBox(20);
        root.setAlignment(Pos.CENTER);
        root.setPadding(new Insets(30));
        root.setStyle("-fx-background-color: #121212;"); 

        Label titleLabel = new Label("Art Forgery Detection Engine");
        titleLabel.setStyle("-fx-font-size: 24px; -fx-font-weight: bold; -fx-text-fill: #FFFFFF;");

        imagePreview = new ImageView();
        imagePreview.setFitWidth(400);
        imagePreview.setFitHeight(300);
        imagePreview.setPreserveRatio(true);
        imagePreview.setStyle("-fx-effect: dropshadow(three-pass-box, rgba(0,0,0,0.8), 10, 0, 0, 0);");

        Button chooseButton = new Button("Select Canvas Image");
        styleButton(chooseButton, "#333333", "#FFFFFF");
        chooseButton.setOnAction(e -> chooseImage(primaryStage));

        analyzeButton = new Button("Analyze Canvas");
        styleButton(analyzeButton, "#1976D2", "#FFFFFF");
        analyzeButton.setDisable(true);
        analyzeButton.setOnAction(e -> analyzeCanvas());

        loadingSpinner = new ProgressIndicator();
        loadingSpinner.setVisible(false); 
        loadingSpinner.setPrefSize(30, 30);

        statusLabel = new Label("Awaiting image selection...");
        statusLabel.setStyle("-fx-text-fill: #AAAAAA; -fx-font-size: 14px;");

        scoreLabel = new Label("");
        scoreLabel.setStyle("-fx-font-size: 32px; -fx-font-weight: bold; -fx-text-fill: #00E676;"); 

        root.getChildren().addAll(
                titleLabel, 
                imagePreview, 
                chooseButton, 
                analyzeButton, 
                loadingSpinner, 
                statusLabel, 
                scoreLabel
        );

        Scene scene = new Scene(root, 800, 600);
        primaryStage.setScene(scene);
        primaryStage.setResizable(false);
        primaryStage.show();
    }

    private void chooseImage(Stage stage) {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Select Artwork");
        fileChooser.getExtensionFilters().addAll(
                new FileChooser.ExtensionFilter("Image Files", "*.png", "*.jpg", "*.jpeg")
        );

        File file = fileChooser.showOpenDialog(stage);
        if (file != null) {
            selectedFile = file;
            Image image = new Image(file.toURI().toString());
            imagePreview.setImage(image);
            
            scoreLabel.setText("");
            statusLabel.setText("Image loaded. Ready for analysis.");
            analyzeButton.setDisable(false);
        }
    }

    
    private void analyzeCanvas() {
        if (selectedFile == null) return;

        analyzeButton.setDisable(true);
        loadingSpinner.setVisible(true);
        statusLabel.setText("Uploading and analyzing... Please wait.");
        scoreLabel.setText("");

        CompletableFuture.runAsync(() -> {
            try {
                String boundary = "---JavaFXBoundary" + System.currentTimeMillis();
                byte[] multipartBody = buildMultipartBody(selectedFile, boundary);

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(SERVER_URL))
                        .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                        .POST(HttpRequest.BodyPublishers.ofByteArray(multipartBody))
                        .build();

                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

                Platform.runLater(() -> handleServerResponse(response));

            } catch (Exception e) {
                Platform.runLater(() -> {
                    loadingSpinner.setVisible(false);
                    statusLabel.setText("Error: Could not connect to the server.");
                    statusLabel.setStyle("-fx-text-fill: #FF5252;"); 
                    analyzeButton.setDisable(false);
                });
            }
        });
    }

    
    private void handleServerResponse(HttpResponse<String> response) {
        loadingSpinner.setVisible(false);
        analyzeButton.setDisable(false);

        if (response.statusCode() == 200) {
            try {
                JSONObject jsonResponse = new JSONObject(response.body());
                double score = jsonResponse.getDouble("authenticity_score");
                
                statusLabel.setText("Analysis Complete!");
                statusLabel.setStyle("-fx-text-fill: #AAAAAA;"); 
                
                scoreLabel.setText(String.format("Authenticity Score: %.1f%%", score));
            } catch (Exception e) {
                statusLabel.setText("Error: Failed to parse server response.");
                statusLabel.setStyle("-fx-text-fill: #FF5252;");
            }
        } else {
            statusLabel.setText("Server Error: " + response.statusCode());
            statusLabel.setStyle("-fx-text-fill: #FF5252;");
        }
    }

    
    private byte[] buildMultipartBody(File file, String boundary) throws IOException {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        
        outputStream.write(("--" + boundary + "\r\n").getBytes());
        outputStream.write(("Content-Disposition: form-data; name=\"file\"; filename=\"" + file.getName() + "\"\r\n").getBytes());
        outputStream.write(("Content-Type: application/octet-stream\r\n\r\n").getBytes());
        
        byte[] fileBytes = Files.readAllBytes(file.toPath());
        outputStream.write(fileBytes);
        
        outputStream.write(("\r\n--" + boundary + "--\r\n").getBytes());
        
        return outputStream.toByteArray();
    }

    
    private void styleButton(Button button, String bgColor, String textColor) {
        button.setStyle(
            "-fx-background-color: " + bgColor + ";" +
            "-fx-text-fill: " + textColor + ";" +
            "-fx-font-size: 14px;" +
            "-fx-font-weight: bold;" +
            "-fx-padding: 10 20 10 20;" +
            "-fx-background-radius: 5;"
        );
        button.setOnMouseEntered(e -> button.setOpacity(0.8));
        button.setOnMouseExited(e -> button.setOpacity(1.0));
    }

    public static void main(String[] args) {
        launch(args);
    }
}