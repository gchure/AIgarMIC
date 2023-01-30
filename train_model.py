#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: 	train_model.py
# Author: 	Alessandro Gerada
# Date: 	2023-01-29
# Copyright: 	Alessandro Gerada 2023
# Email: 	alessandro.gerada@liverpool.ac.uk

"""This script trains an image annotation model"""

import pickle, os, cv2 
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import argparse
import pathlib

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential

def main(): 
    parser = argparse.ArgumentParser("""
    This script loads images from annotations directory and trains ML
    model. Loading from pickled data is not yet implemented
    """)
    parser.add_argument("-p", "--pickled", action="store_true", help="Load data from pickled (.p) files - NOT IMPLEMENTED")
    parser.add_argument("-v", "--visualise", action="store_true", help="Generate visualisations for model diagnostics")
    parser.add_argument("-s", "--save", type=str, help="If specified, tensorflow model will be saved to this folder")
    args = parser.parse_args()

    ANNOTATIONS_FOLDER = "annotations/"
    TRAIN_SPLIT = 0.8
    VALIDATION_SPLIT = 0.2

    # load annotation pickles from annotations/ folder
    if args.pickled: 
        annotation_pickles = os.listdir(ANNOTATIONS_FOLDER)
        annotation_pickles = [path for path in annotation_pickles if path.rfind(".p") > 0]
        image_data = []
        annotation_data = []
        for p in annotation_pickles: 
            pickle_path = os.path.join(ANNOTATIONS_FOLDER, p)
            with open(pickle_path, "rb") as f: 
                temp_images = pickle.load(f)
                temp_annotations = pickle.load(f)
            for i in temp_images: 
                image_data.append(i)
            for a in temp_annotations: 
                annotation_data.append(a)
        raise NotImplementedError("Loading from pickled data is not yet implemented")

    else: 
        annotated_images = pathlib.Path(ANNOTATIONS_FOLDER)
        print(len(list(annotated_images.glob('*/*.jpg'))))
        
        image_height = 160
        image_width = 160
        train_dataset = tf.keras.utils.image_dataset_from_directory(
            annotated_images, 
            validation_split=VALIDATION_SPLIT, 
            subset='training', 
            seed=12345, 
            image_size=(image_height, image_width), 
            batch_size=32
        )
        val_dataset = tf.keras.utils.image_dataset_from_directory(
            annotated_images, 
            validation_split=VALIDATION_SPLIT, 
            subset='validation', 
            seed=12345, 
            image_size=(image_height, image_width), 
            batch_size=32
        )
        print(f"Found the following labels/classes: {train_dataset.class_names}")
        class_names = train_dataset.class_names

        if args.visualise: 
            plt.figure(figsize=(10, 10))
            for images, labels in train_dataset.take(1):
                for i in range(9):
                    ax = plt.subplot(3, 3, i + 1)
                    plt.imshow(images[i].numpy().astype("uint8"))
                    plt.title(class_names[labels[i]])
                    plt.axis("off")
        
        num_classes = len(class_names)

        data_augmentation = Sequential([
            layers.RandomFlip("horizontal",
                            input_shape=(image_height,
                                        image_width,
                                        3)),
            layers.RandomRotation(0.1),
            layers.RandomZoom(0.1),
        ])
        
        model = Sequential([
        data_augmentation, 
        layers.Rescaling(1./255, input_shape=(image_height, image_width, 3)),
        layers.Conv2D(16, 3, padding='same', activation='relu'),
        layers.MaxPooling2D(),
        layers.Conv2D(32, 3, padding='same', activation='relu'),
        layers.MaxPooling2D(),
        layers.Conv2D(64, 3, padding='same', activation='relu'),
        layers.MaxPooling2D(),
        #layers.Dropout(0.2), 
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dense(num_classes)
        ])

        model.compile(optimizer='adam',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
              metrics=['accuracy'])

        model.summary()

        epochs=10
        history = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=epochs
        )

        if args.visualise: 
            acc = history.history['accuracy']
            val_acc = history.history['val_accuracy']

            loss = history.history['loss']
            val_loss = history.history['val_loss']

            epochs_range = range(epochs)

            plt.figure(figsize=(8, 8))
            plt.subplot(1, 2, 1)
            plt.plot(epochs_range, acc, label='Training Accuracy')
            plt.plot(epochs_range, val_acc, label='Validation Accuracy')
            plt.legend(loc='lower right')
            plt.title('Training and Validation Accuracy')

            plt.subplot(1, 2, 2)
            plt.plot(epochs_range, loss, label='Training Loss')
            plt.plot(epochs_range, val_loss, label='Validation Loss')
            plt.legend(loc='upper right')
            plt.title('Training and Validation Loss')
            plt.show()

            if args.save: 
                if not os.path.exists(args.save): 
                    os.mkdir(args.save)
                model.save(args.save)
                
    # preprocessing to convert to tensorflow/keras
    annotation_data = keras.utils.to_categorical(annotation_data)

    # resize
    image_data = [cv2.resize(i, (160, 160)) for i in image_data]
    # convert from BGR to RGB
    image_data = [cv2.cvtColor(i, cv2.COLOR_BGR2RGB) for i in image_data]
    image_data = [i.reshape(1, 160, 160, 3) for i in image_data]
    image_data = [i.astype(np.float32) for i in image_data]

    dataset_tf = tf.data.Dataset.from_tensor_slices((image_data, annotation_data))
    data_n = len(dataset_tf)
    dataset_tf = dataset_tf.shuffle(data_n + 1)

    train_dataset = dataset_tf.take(round(data_n * TRAIN_SPLIT))
    test_dataset = dataset_tf.skip(round(data_n * TRAIN_SPLIT))
    for i,j in train_dataset: 
        print(j)
    
    model = Sequential([

    ])

    model.compile(optimizer='adam',
              loss=tf.keras.losses.CategoricalCrossentropy,
              metrics=['accuracy'])

    #print(model.summary())

    epochs = 10
    history = model.fit(
        train_dataset, 
        validation_data=test_dataset, 
        epochs=epochs
    )
if __name__ == "__main__": 
    main()