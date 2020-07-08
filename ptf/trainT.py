import sys
from collections import namedtuple
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

import data.data as data
import model.model as model
import tensorflow as tf

####################################################################################
Params = namedtuple('Params', ('vocab', 'trainData', 'validationData', 'hidden', 'wordVecSize',
                               'batchSize', 'modelFile', 'maxEpochs', 'gpu', 'callback', 'optimizer',
                               'features', 'trainSize', 'validationSize'),
                    defaults=(None, None, None, 100, 100, 128, None, 10, False, None, 'adam', None, 0, 0))


####################################################################################


def trainModel(params):
    if params.features is None:
        assert params.vocab, "No vocab provided"
    assert params.trainData, "No trainData"
    assert params.validationData, "No validationData"
    assert params.modelFile, "No modelFile provided"

    if params.features is None:
        print("Vocab size     :", len(params.vocab))
        v_size = len(params.vocab)
    else:
        print("Features count :", params.features.len())
        v_size = params.features.len()
    print("Hidden layer   :", params.hidden)
    print("Word vec size  :", params.wordVecSize)
    print("Use GPU        :", params.gpu)
    print("Batch Size     :", params.batchSize)
    print("Models out dir :", params.modelFile)
    print("Train Data     :", params.trainSize)
    print("Validation Data:", params.validationSize)

    strategy = tf.distribute.MirroredStrategy()
    print('Number of devices: {}'.format(strategy.num_replicas_in_sync), file=sys.stderr)

    with strategy.scope():
        m = model.init(vocabularySize=v_size,
                       punctuationSize=len(data.PUNCTUATION_VOCABULARY),
                       hidden=params.hidden,
                       word_vector_size=params.wordVecSize,
                       optimizer=params.optimizer,
                       gpu=params.gpu, use_features=params.features is not None)
        m.summary(150)
        # keras.utils.plot_model(m, 'punc.png')
        # keras.utils.plot_model(m, 'punc_full.png', show_shapes=True)

        print("Training", file=sys.stderr)

        checkpoint = ModelCheckpoint(filepath=params.modelFile,
                                     monitor='loss',
                                     verbose=1,
                                     save_best_only=False,
                                     mode='min',
                                     save_freq=int(params.trainSize / params.batchSize))
        es = EarlyStopping(monitor='val_loss', mode='min', verbose=1)
        callbacks = [checkpoint, es]
        if params.callback is not None:
            callbacks.insert(0, params.callback)

        return m.fit(x=params.trainData,
                     validation_data=params.validationData,
                     epochs=params.maxEpochs,
                     verbose=1,
                     callbacks=callbacks,
                     steps_per_epoch=int(params.trainSize / params.batchSize),
                     validation_steps=int(params.validationSize / params.batchSize))
