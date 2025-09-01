import { ElevenLabsAPI } from 'elevenlabs';

export interface VoiceMessage {
  text: string;
  voiceId?: string;
  model?: string;
}

export interface AudioResponse {
  audioData: Buffer;
  duration: number;
  format: string;
  voiceId: string;
}

export interface TranscriptionResult {
  text: string;
  confidence: number;
  language: string;
  duration: number;
}

export class ElevenLabsService {
  private client: ElevenLabsAPI;
  private defaultVoiceId: string;
  private defaultModel: string;

  constructor() {
    const apiKey = process.env.ELEVENLABS_API_KEY;
    if (!apiKey) {
      throw new Error('ELEVENLABS_API_KEY environment variable is required');
    }

    this.client = new ElevenLabsAPI({
      apiKey: apiKey,
    });

    // Default voice and model - can be made configurable
    this.defaultVoiceId = '21m00Tcm4TlvDq8ikWAM'; // Rachel voice
    this.defaultModel = 'eleven_monolingual_v1';
  }

  async generateSpeech(message: VoiceMessage): Promise<AudioResponse> {
    try {
      const voiceId = message.voiceId || this.defaultVoiceId;
      const model = message.model || this.defaultModel;

      // Generate speech using ElevenLabs API
      const audioStream = await this.client.generate({
        voice: voiceId,
        text: message.text,
        model_id: model,
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.5,
        },
      });

      // Convert stream to buffer
      const chunks: Uint8Array[] = [];
      const reader = audioStream.getReader();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
      }

      const audioData = Buffer.concat(chunks);

      // Estimate duration (rough calculation based on text length)
      // Approximately 150 words per minute, so ~2.5 words per second
      const wordCount = message.text.split(/\s+/).length;
      const estimatedDuration = (wordCount / 2.5) * 1000; // in milliseconds

      return {
        audioData,
        duration: estimatedDuration,
        format: 'mp3',
        voiceId,
      };

    } catch (error) {
      console.error('ElevenLabs TTS error:', error);
      throw new Error(`Failed to generate speech: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async transcribeAudio(audioData: Buffer, options?: {
    language?: string;
    model?: string;
  }): Promise<TranscriptionResult> {
    try {
      // For now, we'll use a simple approach since ElevenLabs focuses on TTS
      // In a production system, you might want to integrate with a dedicated STT service like Whisper

      // This is a placeholder implementation
      // Real transcription would require audio upload and processing
      console.warn('ElevenLabs transcription is not fully implemented. Consider using OpenAI Whisper for STT.');

      return {
        text: '[Transcription not available - ElevenLabs focuses on TTS]',
        confidence: 0,
        language: options?.language || 'en',
        duration: 0,
      };

    } catch (error) {
      console.error('ElevenLabs transcription error:', error);
      throw new Error(`Failed to transcribe audio: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getAvailableVoices(): Promise<any[]> {
    try {
      const voices = await this.client.getVoices();
      return voices;
    } catch (error) {
      console.error('Error fetching voices:', error);
      return [];
    }
  }

  async generateCoachingAudio(
    coachingText: string,
    urgency: 'low' | 'medium' | 'high' = 'medium'
  ): Promise<AudioResponse> {
    // Adjust voice settings based on urgency
    let voiceSettings = {
      stability: 0.5,
      similarity_boost: 0.5,
    };

    let selectedVoiceId = this.defaultVoiceId;

    switch (urgency) {
      case 'high':
        voiceSettings = {
          stability: 0.3, // More dynamic for urgent messages
          similarity_boost: 0.7,
        };
        // Could use a different voice for urgent messages
        break;
      case 'low':
        voiceSettings = {
          stability: 0.7, // More stable for calm messages
          similarity_boost: 0.3,
        };
        break;
      default:
        // Medium urgency - use default settings
        break;
    }

    try {
      const audioStream = await this.client.generate({
        voice: selectedVoiceId,
        text: coachingText,
        model_id: this.defaultModel,
        voice_settings: voiceSettings,
      });

      // Convert stream to buffer
      const chunks: Uint8Array[] = [];
      const reader = audioStream.getReader();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
      }

      const audioData = Buffer.concat(chunks);

      // Estimate duration
      const wordCount = coachingText.split(/\s+/).length;
      const estimatedDuration = (wordCount / 2.5) * 1000;

      return {
        audioData,
        duration: estimatedDuration,
        format: 'mp3',
        voiceId: selectedVoiceId,
      };

    } catch (error) {
      console.error('ElevenLabs coaching audio generation error:', error);
      throw new Error(`Failed to generate coaching audio: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Utility method to create different types of coaching messages
  createCoachingMessage(
    type: 'performance' | 'warning' | 'celebration' | 'instruction',
    content: string
  ): VoiceMessage {
    const prefixes = {
      performance: 'Performance analysis: ',
      warning: 'Warning: ',
      celebration: 'Great job! ',
      instruction: 'Instruction: ',
    };

    return {
      text: `${prefixes[type]}${content}`,
      voiceId: this.defaultVoiceId,
      model: this.defaultModel,
    };
  }
}

// Export singleton instance
export const elevenLabsService = new ElevenLabsService();
