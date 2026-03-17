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
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;
import javafx.stage.FileChooser;
import javafx.stage.Stage;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.util.Base64;
import java.util.concurrent.CompletableFuture;

public class ArtForgeryDetectionApp extends Application {

    private File selectedFile;
    private ImageView originalPreview;
    private ImageView heatmapPreview;
    private Button analyzeButton;
    private ProgressIndicator loadingSpinner;
    private Label statusLabel;
    
    // Score Labels
    private Label finalScoreLabel;
    private Label cnnScoreLabel;
    private Label vitScoreLabel;
    private Label hybridScoreLabel;

    private static final HttpClient httpClient = HttpClient.newHttpClient();
    private static final String SERVER_URL = "http://localhost:5000/analyze";

    @Override
    public void start(Stage primaryStage) {
        primaryStage.setTitle("Art Forgery Detection Engine - V2 Advanced");

        VBox root = new VBox(20);
        root.setAlignment(Pos.CENTER);
        root.setPadding(new Insets(30));
        root.setStyle("-fx-background-color: #121212; -fx-font-family: 'Segoe UI', sans-serif;"); 

        // --- IMAGE DISPLAY AREA (Side by Side) ---
        HBox imageBox = new HBox(20);
        imageBox.setAlignment(Pos.CENTER);

        originalPreview = setupImageView();
        heatmapPreview = setupImageView();
        
        VBox originalBox = new VBox(5, new Label("Original Canvas"){{ setStyle("-fx-text-fill: #AAAAAA;"); }}, originalPreview);
        originalBox.setAlignment(Pos.CENTER);
        
        VBox heatmapBox = new VBox(5, new Label("XAI Activation Map"){{ setStyle("-fx-text-fill: #AAAAAA;"); }}, heatmapPreview);
        heatmapBox.setAlignment(Pos.CENTER);

        imageBox.getChildren().addAll(originalBox, heatmapBox);

        // --- CONTROLS ---
        HBox controlsBox = new HBox(15);
        controlsBox.setAlignment(Pos.CENTER);

        Button chooseButton = new Button("Select Canvas Image");
        styleButton(chooseButton, "#333333", "#FFFFFF");
        chooseButton.setOnAction(e -> chooseImage(primaryStage));

        analyzeButton = new Button("Analyze Canvas");
        styleButton(analyzeButton, "#1976D2", "#FFFFFF");
        analyzeButton.setDisable(true);
        analyzeButton.setOnAction(e -> analyzeCanvas());

        controlsBox.getChildren().addAll(chooseButton, analyzeButton);

        // --- STATUS & LOADING ---
        HBox statusBox = new HBox(10);
        statusBox.setAlignment(Pos.CENTER);
        
        loadingSpinner = new ProgressIndicator();
        loadingSpinner.setVisible(false); 
        loadingSpinner.setPrefSize(20, 20);

        statusLabel = new Label("Awaiting image selection...");
        statusLabel.setStyle("-fx-text-fill: #AAAAAA; -fx-font-size: 14px;");
        
        statusBox.getChildren().addAll(loadingSpinner, statusLabel);

        // --- SCORES AREA ---
        VBox scoresBox = new VBox(5);
        scoresBox.setAlignment(Pos.CENTER);
        scoresBox.setStyle("-fx-background-color: #1E1E1E; -fx-padding: 15; -fx-background-radius: 10;");

        finalScoreLabel = new Label("");
        finalScoreLabel.setStyle("-fx-font-size: 24px; -fx-font-weight: bold; -fx-text-fill: #00E676;"); 
        
        cnnScoreLabel = new Label("");
        vitScoreLabel = new Label("");
        hybridScoreLabel = new Label("");
        String subScoreStyle = "-fx-font-size: 14px; -fx-text-fill: #BBBBBB;";
        cnnScoreLabel.setStyle(subScoreStyle);
        vitScoreLabel.setStyle(subScoreStyle);
        hybridScoreLabel.setStyle(subScoreStyle);

        scoresBox.getChildren().addAll(finalScoreLabel, cnnScoreLabel, vitScoreLabel, hybridScoreLabel);

        // --- ASSEMBLE ---
        root.getChildren().addAll(
                imageBox, 
                controlsBox, 
                statusBox, 
                scoresBox
        );

        Scene scene = new Scene(root, 900, 750);
        primaryStage.setScene(scene);
        primaryStage.setResizable(false);
        primaryStage.show();
    }

    private ImageView setupImageView() {
        ImageView iv = new ImageView();
        iv.setFitWidth(350);
        iv.setFitHeight(350);
        iv.setPreserveRatio(true);
        iv.setStyle("-fx-effect: dropshadow(three-pass-box, rgba(0,0,0,0.8), 10, 0, 0, 0); -fx-border-color: #333333; -fx-border-width: 2px;");
        return iv;
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
            originalPreview.setImage(image);
            heatmapPreview.setImage(null); 
            
            clearScores();
            statusLabel.setText("Image loaded. Ready for Triple-Branch Analysis.");
            statusLabel.setStyle("-fx-text-fill: #AAAAAA;");
            analyzeButton.setDisable(false);
        }
    }

    private void analyzeCanvas() {
        if (selectedFile == null) return;

        analyzeButton.setDisable(true);
        loadingSpinner.setVisible(true);
        statusLabel.setText("Extracting patches & querying Neural Network... (This may take a moment)");
        statusLabel.setStyle("-fx-text-fill: #FFCA28;"); 
        clearScores();

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
                    statusLabel.setText("Error: Could not reach the Python Backend. Is Flask running?");
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
                JSONObject json = new JSONObject(response.body());
                
                double finalScore = json.getDouble("final_score");
                double cnn = json.getDouble("cnn_confidence");
                double vit = json.getDouble("vit_confidence");
                double hybrid = json.getDouble("hybrid_confidence");
                String heatmapBase64 = json.getString("heatmap_image");
                
                statusLabel.setText("Analysis Complete: " + json.optString("message", "Success"));
                statusLabel.setStyle("-fx-text-fill: #00E676;"); 
                
                if (heatmapBase64 != null && !heatmapBase64.isEmpty()) {
                    byte[] imageBytes = Base64.getDecoder().decode(heatmapBase64);
                    Image heatmapImg = new Image(new ByteArrayInputStream(imageBytes));
                    heatmapPreview.setImage(heatmapImg);
                }

                finalScoreLabel.setText(String.format("Final Forgery Probability: %.1f%%", finalScore));
                
                if (finalScore > 50.0) {
                    finalScoreLabel.setStyle("-fx-font-size: 24px; -fx-font-weight: bold; -fx-text-fill: #FF5252;"); 
                } else {
                    finalScoreLabel.setStyle("-fx-font-size: 24px; -fx-font-weight: bold; -fx-text-fill: #00E676;"); 
                }

                cnnScoreLabel.setText(String.format("CNN (Texture/Edges): %.1f%%", cnn));
                vitScoreLabel.setText(String.format("Swin-ViT (Global Context): %.1f%%", vit));
                hybridScoreLabel.setText(String.format("Hybrid Engine: %.1f%%", hybrid));

            } catch (Exception e) {
                statusLabel.setText("Error: Failed to parse Python response.");
                statusLabel.setStyle("-fx-text-fill: #FF5252;");
                System.out.println(e.getMessage());
            }
        } else {
            statusLabel.setText("Server Error: " + response.statusCode());
            statusLabel.setStyle("-fx-text-fill: #FF5252;");
        }
    }

    private byte[] buildMultipartBody(File file, String boundary) throws IOException {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        
        outputStream.write(("--" + boundary + "\r\n").getBytes());
        outputStream.write(("Content-Disposition: form-data; name=\"image\"; filename=\"" + file.getName() + "\"\r\n").getBytes());
        outputStream.write(("Content-Type: application/octet-stream\r\n\r\n").getBytes());
        
        byte[] fileBytes = Files.readAllBytes(file.toPath());
        outputStream.write(fileBytes);
        
        outputStream.write(("\r\n--" + boundary + "--\r\n").getBytes());
        
        return outputStream.toByteArray();
    }

    private void clearScores() {
        finalScoreLabel.setText("");
        cnnScoreLabel.setText("");
        vitScoreLabel.setText("");
        hybridScoreLabel.setText("");
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
        button.setOnMouseEntered(e -> button.setStyle(button.getStyle().replace(bgColor, "#555555")));
        button.setOnMouseExited(e -> button.setStyle(button.getStyle().replace("#555555", bgColor)));
    }

    public static void main(String[] args) {
        launch(args);
    }
}