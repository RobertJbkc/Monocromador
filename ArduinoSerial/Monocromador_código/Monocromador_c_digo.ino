#define dir 12  // CW+ no TB6560 Liga_desliga o rele: "1" (cresce lambda) / "0" (diminue lambda)
#define passo 3 // CK+ no TB6560
#define enable 9  // EN+ no TB6560
#define rele 6 // Liga_desliga o rele: "1" (desligado) / "0" (ligado)
#define on_off 10

int sensor0 = A0; // Final de curso --> Pequenos comprimentos
int sensor0Value = 0;

int sensor1 = A1; // Final de curso --> Grandes comprimentos
int sensor1Value = 0;

int sensor3 = A3; // Liga e desliga o sistema (botão: on/off)
int sensor3Value = 0;

int sensor5 = A5; // Define medida e retorno manual
int sensor5Value = 0;

int sensor6 = A6; // Define a velocidade do motor manualmente --> Joystick de velocidade
int sensor6Value = 0;

int sensor7 = A7; // Aumenta e diminui o comprimento de onda --> Joystick de direção
int sensor7Value = 0;

int sensorDelay = 3; // ms
int tempo1, tempo2, tempo3, x, r;


void setup() {
//  INPUT_PULLUP --> Botões em portas digitais
  Serial.begin(9600);
  pinMode(dir, OUTPUT);
  pinMode(passo, OUTPUT);
  pinMode(enable, OUTPUT);
  pinMode(rele, OUTPUT);
  pinMode(on_off, OUTPUT);
//  digitalWrite(dir,0); // "1" - cresce comprimento de onda / "0" - diminui comprimento de onda
  digitalWrite(passo,0);
  digitalWrite(enable,0);
//  digitalWrite(rele, 0); // "0" - habilita o TB6560 / "1" - desabilita o TB6560

}


void medir() {
  if(sensor5Value < 1000) {
    digitalWrite(on_off, 1);
    digitalWrite(rele,0);
    digitalWrite(dir,0);
    sensor6Value = analogRead(sensor6); // Determina a velocidade do motor para medida
    delay(sensorDelay);
    tempo2 = int(sensor6Value/8+6/8);
    tempo3= 128 - tempo2;

    if(Serial.available() > 0) {
      int ppr = Serial.parseInt();
      for (int r=0; r<ppr; r++){
        digitalWrite(passo,1);
        delay(tempo3);
        digitalWrite(passo,0);
        delay(tempo3);
        }
      Serial.println(ppr);
      ppr = 0;
    }
  }
}

void determinarTempo() {
  if (sensor5Value > 1000) {
    sensor6Value = analogRead(sensor6); // Determina a velocidade do motor para ajuste manual
    delay(sensorDelay);
    tempo2 = int(sensor6Value/8+6/8);
    tempo1= 128 - tempo2;
  }
  
}

void protecaoFimCurso() {
  sensor0Value = analogRead(sensor0); // Fim de eixo lambda mínimo
  delay(sensorDelay);
  sensor1Value = analogRead(sensor1); // Fim de eixo lambda máximo
  delay(sensorDelay);

  if(sensor0Value > 1000) {
    digitalWrite(rele,0);
    digitalWrite(dir,1);
    while(sensor0Value) {
      sensor0Value = analogRead(sensor0);
      delay(sensorDelay);
      digitalWrite(passo,1);
      delay(tempo1);
      digitalWrite(passo,0);
      delay(tempo1);
    }
  }
  
  if(sensor1Value > 1000) {
    digitalWrite(rele,0);
    digitalWrite(dir,0);
    while(sensor1Value) {
      sensor1Value = analogRead(sensor0);
      delay(sensorDelay);
      digitalWrite(passo,1);
      delay(tempo1);
      digitalWrite(passo,0);
      delay(tempo1);
    }
  }
  
}

void loop() {
  determinarTempo();
  protecaoFimCurso();
  medir();

  sensor7Value = analogRead(sensor7);
  delay(3);
  sensor5Value = analogRead(sensor5);
  delay(3);

  if(sensor7Value > 800 and sensor5Value > 1000) {
    digitalWrite(rele,0);
    digitalWrite(dir,0);
    digitalWrite(on_off, 1);
    
    while(sensor7Value > 800) {
      sensor7Value = analogRead(sensor7);
      delay(3);
      digitalWrite(passo,1);
      delay(tempo1);
      digitalWrite(passo,0);
      delay(tempo1);
    }
  }

  if(sensor7Value < 500 and sensor5Value > 1000) {
    digitalWrite(rele,0);
    digitalWrite(dir,1);
    digitalWrite(on_off, 1);

    while(sensor7Value < 500) {
      sensor7Value = analogRead(sensor7);
      delay(3);
      digitalWrite(passo,1);
      delay(tempo1);
      digitalWrite(passo,0);
      delay(tempo1);
    }
  }

  if (sensor7Value > 600 and sensor7Value < 700 and sensor5Value > 1000){
    digitalWrite(rele,1);
    digitalWrite(on_off, 0);
  }
  
}
