import tensorflow as tf
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler, label_binarize
import numpy as np
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import joblib
import ipaddress
import re

class Predict(APIView):
    parser_classes = (MultiPartParser, FormParser) 
    # label_encoder = joblib.load(settings.BASE_DIR / 'mlmodel/tensorflow_model/label_encoder.pkl')

    model_path = settings.BASE_DIR / 'mlmodel/tensorflow_model/no_adv_model3.h5'
    model = tf.keras.models.load_model(model_path)
    required_columns = [
        'source ip', 'source port', 'destination ip', 'destination port',
        'flow duration', 'total length of fwd packets', 'total length of bwd packets',
        'fwd packet length max', 'bwd packet length max', 'bwd packet length mean',
        'flow packets/s', 'flow iat mean', 'flow iat std', 'flow iat max', 'fwd iat total',
        'fwd iat min', 'bwd packets/s', 'max packet length', 'packet length mean',
        'average packet size', 'avg bwd segment size', 'subflow bwd bytes',
        'init_win_bytes_forward', 'init_win_bytes_backward', 'min_seg_size_forward',
        'external ip', 'Month', 'Hour', 'Minute', 'Second'
    ]

    file_param = openapi.Parameter('file', openapi.IN_FORM, description="Upload CSV File", type=openapi.TYPE_FILE, required=True)
    
    @swagger_auto_schema(manual_parameters=[file_param])
    def post(self, request, format=None):
        scaler = joblib.load(settings.BASE_DIR / 'mlmodel/tensorflow_model/scaler.pkl')
        # Read uploaded file
        file_obj = request.FILES['file']
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = pd.read_csv(file_obj)

            data.columns = data.columns.str.strip().str.lower()

            def ip_to_float(ip):
                return int(ipaddress.ip_address(ip))

            # Apply the function to 'Source IP' and 'Destination IP' columns
            data['source ip'] = data['source ip'].apply(ip_to_float)
            data['destination ip'] = data['destination ip'].apply(ip_to_float)
            data['external ip'] = data['external ip'].dropna().apply(ip_to_float)

            # Function to parse timestamp
            def parse_timestamp(timestamp):
                # Regular expression to match different timestamp formats
                regex = r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})[ ,:-](\d{1,2}):(\d{2})(?::(\d{2}))?"
                match = re.match(regex, timestamp)
                if match:
                    month, day, year, hour, minute, second = match.groups()
                    # Handle two-digit years
                    if len(year) == 2:
                        year = "20" + year if int(year) < 50 else "19" + year
                    second = second if second else "00"
                    return int(day), int(month), int(year), int(hour), int(minute), int(second)
                return None

            # Apply the function to 'timestamp' column and create new columns
            data[['Day', 'Month', 'Year', 'Hour', 'Minute', 'Second']] = data['timestamp'].apply(
                lambda x: pd.Series(parse_timestamp(x))
            )

            # Drop rows where timestamp parsing failed
            data.dropna(subset=['Day', 'Month', 'Year', 'Hour', 'Minute', 'Second'], inplace=True)

            # Drop the original 'timestamp' column
            data.drop(columns=['timestamp'], inplace=True)
            
            if not all(column in data.columns for column in self.required_columns):
                return Response({'error': 'Missing required columns in the CSV file'}, status=status.HTTP_400_BAD_REQUEST)



            data_filtered = data[self.required_columns]
            # print(data_filtered)
            # scaler = StandardScaler()
            data_normalized = scaler.transform(data_filtered)
            # print(data_normalized)
            predictions = self.model.predict(data_normalized)
            predicted_classes = np.argmax(predictions, axis=1)
            predicted_labels = [settings.LABELS[i] for i in predicted_classes]

            return Response({'predictions': predicted_labels}, status=status.HTTP_200_OK)
        
        except Exception as e:

            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)