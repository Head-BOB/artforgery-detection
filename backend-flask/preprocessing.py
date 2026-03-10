import cv2
import os

def process_image():
    image_path = input("Enter the full path of the image: ").strip()

    if not os.path.isfile(image_path):
        print("Error: File not found.")
        return

    img = cv2.imread(image_path)

    if img is None:
        print("Error: Could not read the image.")
        return

    # uploads folder inside backend-flask
    upload_folder = os.path.join(os.path.dirname(__file__), "uploads")

    base_filename = os.path.basename(image_path)
    file_name, file_extension = os.path.splitext(base_filename)

    rgb_filename = os.path.join(upload_folder, f"{file_name}_rgb{file_extension}")
    cv2.imwrite(rgb_filename, img)

    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_filename = os.path.join(upload_folder, f"{file_name}_grayscale{file_extension}")
    cv2.imwrite(gray_filename, gray_img)

    edge_img = cv2.Canny(gray_img, 100, 200)
    edge_filename = os.path.join(upload_folder, f"{file_name}_edges{file_extension}")
    cv2.imwrite(edge_filename, edge_img)

    print("\n✅ Images saved successfully in the 'uploads' folder:")
    print(rgb_filename)
    print(gray_filename)
    print(edge_filename)

if __name__ == "__main__":
    process_image()