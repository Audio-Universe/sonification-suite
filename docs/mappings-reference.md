# Output Sound Mappings Reference

Here we provide a reference guide for the sound mapping options that you are able to choose in a Custom Sound style. These are the options listed under ***Output*** in the Custom Style Menu. For more information on how to do produce custom styles see the [User Guide Custom Styles Section](https://sonification-suite.readthedocs.io/en/latest/user-guide/#custom-styles).

Below we describe each of the different ***Output*** sound parameters you can choose from, and how the ***Range*** is treated in each of these cases.

## Time

Every sonification must have some data parameter mapped to time. This is to decide how the sonification will evolve through time. For a time series type sonification (where the data is a function of time), it is very intuitive to map time to time. However, you might also want to map something else to time. For example you might choose to order stars in your sonification in order of their brightness, with the brightest ones heard first. 



By default lower data values will correspond to earlier times. You can select ***Invert Data*** if you wish the highest values to be heard first. 



We do not recommend changing ***Time Range***. 



## Pitch

You can map your data to pitch (i.e., how high or low in frequency the sound is perceived). This is treated differently depending on if you are choosing a ***Continuous*** or ***Discrete*** mode of mapping.



**Discrete Mapping:** 

In this case the data is mapped to the list of notes in the ***Notes*** section of the Custom Style menu. Each data point will be represented by a single note. For example, if you have five notes listed, then the ***Input*** data value will be binned only onto these five notes. By default, the lowest values in the data will be mapped onto the lowest pitched notes and the highest values will be mapped onto the highest pitched notes. The opposite will be true if you select ***Invert data***. 



For Discrete Mapping, If you change ***Pitch Range*** the mapping will only use a subset of the notes in the notes box. For example, if you select the range to be between 0 and 0.5 it will only use the lowest half of the notes listed in the box (although this might not be exact due to exactly how the data is being binned). It is not recommended to use ***Pitch Range*** for Discrete Mapping. It is better to keep this set at 0 to 1 and choose the exact notes you wish to use in the notes box.  



**Continuous Mapping:** In this case there is a continuous mapping between the data and pitch of the sound. Therefore, you do not get distinct individual pitches but a continuous bending, or sliding, up and down of the pitch of the sound. If you have a single note specified in the notes box to the ***Notes*** section a single note will be heard continuously throughout the sonification. If you choose multiple notes, these will all be played simultaneously (e.g., you can create a chord). 



By default the lowest data values are mapped to whatever is specified in the Notes box. However, if you select ***Invert Data*** the opposite will be true. For the default values of 0 to 1.0 in ***Pitch Range*** you will obtain 2 octaves of pitch range, i.e., 24 semitones, between the highest and lowest pitches in the sonification. You can reduce this number by changing the values of ***Pitch Range***. For example, if you select 0 to 0.5 you will only get a single octave. 



## Filter cutoff

You can map your data to control a frequency filter cut off parameter. This is most effective if you have a harmonically rich sound containing multiple sound frequencies, such as a synthesised chord made from a Tri Synth. This parameter removes frequencies of the sound *above* its value. In practice this uses something called a [Butterworth filter](https://en.wikipedia.org/wiki/Butterworth_filter), to create a smoother distribution of the frequency removal. The effect of this is the sound more or less harmonically rich as the value changes. 



By default the lowest data values are mapped to the lowest cutoff frequency values. This means that the sound will contain fewer frequencies (and is perceived as less intense). If the data value is high the sound will contain more frequencies (and is perceived as more in intense). If you select ***Invert Data*** you will get the opposite effect (lower data values will produce a more harmonically rich and intense sound).



By default the cut-off parameter has a minimum value of 20Hz (Note E0) to 20kHz (Note D#10). This corresponds to values of 0 and 1 in the ***Filter Cutoff Range***, respectively.  It can be very common to need to change the ***Filter Cutoff Range*** to get the desired effect, depending on the frequency content of the specific base sound you are using. We would recommend making use of the [Spectrogram feature](../user-guide#spectrogram) on the sonification page to help make these choices. 



## Volume

You can map your data to control the volume of the sound, which in turn will control the perceived loudness of the sound. By default the lowest data values will be the quietest and the highest data values will be the loudest. The opposite will be true if you select ***Invert Data***. By default the ***Volume Range*** goes from 0 (which corresponds to silence) to a value of 1.0 which is the peak volume. 



**Important:** In the current form, only changing the maximum value of ***Volume Range*** will have no perceivable effect. This is because the volume is re-normalised in the final sonification step, to a sensible peak volume. However, if you change the lower value, e.g., to go between 0.3 to 1.0, the lowest data point will be mapped to 30% of the normalised peak volume, and the highest data point to the normalised peak volume.  



## Pan

**This is most directly interpretable for a Stereo sound system.** This parameter affects the perceived spatial location of the sound (left to right). You can use Pan to map your data to the left and right stereo field. By default the lowest data values will be mapped to full left and the highest data values to full right. If you select ***Invert Data*** the opposite will be true. 



You can change the values of ***Pan Range***. A value of 0 means full left, a value of 1 means full right, and a value of 0.5 means centre. Therefore if you changed the range to be between 0 and 0.5, and did not have invert data selected, the lowest datapoints would be heard full left, and the highest data points would be hear full right.



## Azimuth

**This is most applicable for a surround sound system, such as 5.1 and 7.1**. This parameter affects the perceived spatial location of the sound around a circle with respect the listener. 



The data values are scales to azimuth such that by default the lowest value is set 0 degrees (directly in front) and the highest values will be set to 360 degrees (also directly in front). The direct is such that azimuth increases to the left. Therefore:



- 0 degrees is directly in front 

- 90 degrees is directly left 

- 180 degrees is directly behind

- 270 degrees is directly right. 



If ***Invert Data*** is selected, the azimuth will, instead, increase to the right, such that 90 degrees is directly right and 270 degrees is directly left. 



**Important:** It is currently not possibly to change the parameter range of Azimuth.



## Polar Angle

**This is most applicable for a surround sound system, such as 5.1 and 7.1, or ideally systems with speakers off the horizon**. Because most sound systems do not have speakers above or below the observers horizon, a perceivable effect is only really heard if this is used with a sound system with speakers off horizon, or it is used in conjunction with the azimuth parameter.  



The lowest value (0 degrees) corresponds to directly above and the highest value (180 degrees) to directly below, where 90 degrees is on the horizon. If ***Invert Data*** is selected, than this mapping will be inverted, such that 180 degrees is directly above. 



**Important:** It is currently not possibly to change the parameter range of Polar Angle.