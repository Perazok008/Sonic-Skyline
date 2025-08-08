from midi2audio import FluidSynth


def midi_to_audio_wav_file(input_midi_file: str, output_wav_file: str, sf2_path: str, sample_rate: int = 44100):
    fs = FluidSynth(sound_font=sf2_path, sample_rate=sample_rate)
    fs.midi_to_audio(input_midi_file, output_wav_file)


if __name__ == "__main__":
    pass