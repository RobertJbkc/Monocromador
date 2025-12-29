void setup() {
  Serial.begin(9600);          // Inicia comunicação serial a 9600 baud
  pinMode(LED_BUILTIN, OUTPUT); // Configura LED interno como saída
}

void loop() {
  if (Serial.available() > 0) {
    int vezes = Serial.parseInt();                 // Converte string para inteiro [web:1]

    while (Serial.available() > 0) {
      Serial.read(); // Limpar o buffer da Serial
    }
    
    for(int i = 0; i < vezes; i++) {
      digitalWrite(LED_BUILTIN, HIGH);  // LED acende
      delay(200);                       // Espera 300ms
      digitalWrite(LED_BUILTIN, LOW);   // LED apaga
      delay(200);                       // Espera 300ms
    }
    
    Serial.println("Pronto! Digite outro numero:");
  }
}
