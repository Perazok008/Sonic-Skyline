from midi2audio import FluidSynth

input_midi_file = "./audio_files/output.mid"
output_wav_file = "./audio_files/output.wav"

def midi_to_audio_wav_file(input_midi_file, output_wav_file):

    fs = FluidSynth(sound_font='/opt/homebrew/Cellar/fluid-synth/2.4.7/share/fluid-synth/sf2/VintageDreamsWaves-v2.sf2', sample_rate=44100)

    fs.midi_to_audio(input_midi_file, output_wav_file)

midi_to_audio_wav_file(input_midi_file, output_wav_file)