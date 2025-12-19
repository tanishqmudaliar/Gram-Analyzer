import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.gramanalyzer.app',
  appName: 'GramAnalyzer',
  webDir: 'out',
  server: {
    androidScheme: 'https',
    // For development, uncomment and set your local IP
    // url: 'http://192.168.1.x:3000',
    // cleartext: true
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#09090b',
      showSpinner: false,
    },
  },
  android: {
    allowMixedContent: true,
  },
};

export default config;
