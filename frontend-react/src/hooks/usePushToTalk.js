import { useState, useEffect, useRef, useCallback } from 'react';
import { playMicStart, playProcessing, playError } from '../utils/audioCues';

export const usePushToTalk = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      playMicStart(); // Trigger native mic open cue
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        audioChunksRef.current = [];
        
        // CRITICAL: Shut down hardware tracks immediately to stop listening
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }

        // Send to backend endpoint
        try {
          playProcessing(); // Native tone to indicate processing
          
          const formData = new FormData();
          formData.append('file', audioBlob, 'voice_input.webm');
          
          const response = await fetch('http://localhost:8000/api/transcribe', {
            method: 'POST',
            body: formData,
          });
          
          if (!response.ok) {
            throw new Error(`Transcription API failed: ${response.status} ${response.statusText}`);
          }
          
          const data = await response.json();
          if (data.success && data.text) {
            // Append or set the transcript
            setTranscript(prev => prev ? `${prev} ${data.text}` : data.text);
          } else if (data.error) {
            throw new Error(data.error);
          }
        } catch (err) {
          console.error('Transcription error:', err);
          playError(); // Trigger error cue
          setError(err.message);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Microphone error:', err);
      playError(); // Trigger error cue for permission denied
      setError('Microphone access denied or unavailable.');
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  useEffect(() => {
    const handleKeyDown = (event) => {
      // Ignore keypresses if the user is actively typing in an input or textarea
      const targetTag = event.target.tagName.toUpperCase();
      if (targetTag === 'INPUT' || targetTag === 'TEXTAREA') {
        return;
      }
      
      // We only care about the spacebar
      if (event.code === 'Space') {
        // CRITICAL SAFEGUARD: Prevent rapid re-firing if key is held down
        if (event.repeat) return; 
        
        // Prevent default spacebar scrolling
        event.preventDefault(); 
        
        startRecording();
      }
    };

    const handleKeyUp = (event) => {
      // Ignore if releasing spacebar while inside an input field
      const targetTag = event.target.tagName.toUpperCase();
      if (targetTag === 'INPUT' || targetTag === 'TEXTAREA') {
        return;
      }

      if (event.code === 'Space') {
        event.preventDefault();
        stopRecording();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      
      // Cleanup tracks on unmount
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [startRecording, stopRecording]);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setError(null);
  }, []);

  return { isRecording, transcript, error, resetTranscript };
};
