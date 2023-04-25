from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import cv2
import imutils
import numpy as np
import pytesseract
import re

from .models import LicensePlate,Driver

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_license_plate(request):
    if request.method == 'POST' and request.FILES['image']:
        uploaded_image = request.FILES['image']
        fs = FileSystemStorage()
        image_path = fs.save(uploaded_image.name, uploaded_image)

        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        img = cv2.resize(img, (600, 400))

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 13, 15, 15)

        edged = cv2.Canny(gray, 30, 200)
        contours = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        screenCnt = None

        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018 * peri, True)

            if len(approx) == 4:
                screenCnt = approx
                break

        if screenCnt is None:
            detected = 0
            result = "No contour detected"
        else:
            detected = 1
            cv2.drawContours(img, [screenCnt], -1, (0, 0, 255), 3)

        if detected == 1:
            mask = np.zeros(gray.shape, np.uint8)
            new_image = cv2.drawContours(mask, [screenCnt], 0, 255, -1,)
            new_image = cv2.bitwise_and(img, img, mask=mask)

            (x, y) = np.where(mask == 255)
            (topx, topy) = (np.min(x), np.min(y))
            (bottomx, bottomy) = (np.max(x), np.max(y))
            cropped = gray[topx:bottomx + 1, topy:bottomy + 1]

        else:
            cropped = gray

        text = pytesseract.image_to_string(cropped, config='--psm 11')

        text = re.search(r'([A-Z]{3}-\w{5})|([A-Z]{3}-\w{5})', text)

        if text:
            plate_number = text.group(0)
            try:
                # check if license plate exists in database
                plate_obj = LicensePlate.objects.filter(plate_number=plate_number).first()
                
                if plate_obj:
                    driver_obj = Driver.objects.filter(license_plate=plate_obj).first()
                    result= "Detected license plate Number is: " + plate_number + "\nDriver Name: " + driver_obj.name + "\nAddress: " + driver_obj.address
                   
                else:
                    # create new LicensePlate object if not found in database
                    plate_obj = LicensePlate(image=uploaded_image, plate_number=plate_number)
                    plate_obj.save()
                    result = "Detected license plate Number is: " + plate_number
            except Exception as e:
                result = "An error occurred while saving the license plate: " + str(e)
        else:
            result = "License plate not found in the required format."


        img = cv2.resize(img, (500, 300))
        cropped = cv2.resize(cropped, (400, 200))
        cv2.imwrite(image_path, img)
        cv2.imwrite('cropped.jpg', cropped)

        context = {'result': result, 'image_path': image_path}

        return render(request, 'upload.html', context)

    return render(request, 'upload.html')
