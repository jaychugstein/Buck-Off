#pragma GCC optimize ("no-inline-functions-called-once", "no-reorder-blocks", "no-align-functions", "no-tree-loop-optimize", "no-inline-small-functions", "no-split-wide-types", "no-tree-pre", "no-code-hoisting", "no-ipa-sra", "no-tree-loop-im")   // keeps the game small enough to fit with plain Arduino settings
// BUCK OFF - stay on the bull as long as you can. A prompt pops up next to the bull: press that button
// before it runs out and the bull bucks; miss it (or press the wrong one) and the cowboy slips.
// Three slips and he's bucked off. It gets faster the longer you ride.
#include <Arduboy2.h>
#include "font.h"
#include <ArduboyFX.h>
#include <avr/eeprom.h>
#include "fxdata.h"
#include "tables.h"
#include <ArduboyTones.h>
Arduboy2Base ab;
ARDUBOY_NO_USB
ArduboyTones snd(ab.audio.enabled);

// ---------------------------------------------------------------- text (5x7 font straight into the screen buffer)
int16_t tx_, ty_; bool tw_;
void at(int16_t x, int16_t y) { tx_ = x; ty_ = y; }
void glyph(uint8_t g) {
  for (uint8_t i = 0; i < 6; i++, tx_++) {
    if (tx_ < 0 || tx_ > 127) continue;
    uint8_t b = i < 5 ? pgm_read_byte(FONT + g * 5 + i) : 0;
    if (!b) continue;
    int16_t p = ty_ >> 3; uint8_t o = ty_ & 7;
    uint8_t lo = b << o, hi = o ? b >> (8 - o) : 0;
    uint8_t* q = ab.sBuffer + p * 128 + tx_;
    if (p < 8) { if (tw_) *q |= lo; else *q &= ~lo; }
    if (hi && p < 7) { q += 128; if (tw_) *q |= hi; else *q &= ~hi; }
  }
}
void pc(char c) { glyph(c == '\x18' ? 60 : c == '\x19' ? 61 : (c >= 32 && c <= 90) ? c - 32 : 0); }
void pp(PGM_P s) { char c; while ((c = pgm_read_byte(s++))) pc(c); }
void pn(int32_t v) { char b[11]; uint8_t n = 0; do { b[n++] = '0' + v % 10; v /= 10; } while (v); while (n) pc(b[--n]); }
void secs(uint16_t t) { pn(t / 10); pc('.'); pn(t % 10); }                    // tenths of a second -> "23.4"
void boldC(int16_t cx, int16_t y, PGM_P s) {                                   // bold, centred on cx
  int16_t x = cx - strlen_P(s) * 7 / 2;
  for (char c; (c = pgm_read_byte(s++)); x += 7) { at(x, y); pc(c); at(x + 1, y); pc(c); }
}
// tiny 3x5 letters and digits (black)
const uint8_t TINY[] PROGMEM = {31,17,31, 0,31,0, 29,21,23, 21,21,31, 7,4,31, 23,21,29, 31,21,29, 1,1,31, 31,21,31, 23,21,31,
  30,5,30, 31,21,10, 14,17,17, 31,17,14, 31,21,17, 31,5,1, 14,17,29, 31,4,31, 17,31,17, 8,16,15, 31,4,27, 31,16,16, 31,2,31,
  31,1,30, 14,17,14, 31,5,2, 14,17,30, 31,5,26, 18,21,9, 1,31,1, 15,16,15, 7,24,7, 31,8,31, 27,4,27, 3,28,3, 25,21,19,
  4,14,4, 0,0,0, 0,23,0, 0,16,0, 25,4,19, 0,10,0, 0,3,0, 16,8,0};
void tiny(int16_t x, int16_t y, uint8_t g) {
  for (uint8_t i = 0; i < 3; i++) {
    uint8_t b = pgm_read_byte(TINY + g * 3 + i); int16_t xx = x + i;
    if (xx < 0 || xx > 127 || y < 0 || y > 59) continue;
    uint8_t* q = ab.sBuffer + (y >> 3) * 128 + xx; uint8_t o = y & 7;
    *q &= ~(b << o); if (o > 3 && (y >> 3) < 7) q[128] &= ~(b >> (8 - o));
  }
}
uint8_t tinyIdx(char c) {
  return c >= '0' && c <= '9' ? c - '0' : c >= 'A' && c <= 'Z' ? c - 'A' + 10 : c == '+' ? 36 : c == '!' ? 38 : c == '.' ? 39 : c == '%' ? 40 : c == ':' ? 41 : c == '\'' ? 42 : c == ',' ? 43 : 37;
}
// M, W and N are drawn wider (5, 5 and 4 columns) so they read clearly; spaces are narrower
const uint8_t WIDE[] PROGMEM = { 31,2,4,2,31,  31,8,4,8,31,  31,2,4,31 };   // M W N
int16_t tinyChar(int16_t x, int16_t y, char c) {                            // draws one letter, returns where the next one goes
  if (c == 'M' || c == 'W' || c == 'N') {
    uint8_t o = c == 'M' ? 0 : c == 'W' ? 5 : 10, w = c == 'N' ? 4 : 5;
    for (uint8_t i = 0; i < w; i++) {
      int16_t xx = x + i; if (xx < 0 || xx > 127 || y < 0 || y > 59) continue;
      uint8_t b = pgm_read_byte(WIDE + o + i); uint8_t* q = ab.sBuffer + (y >> 3) * 128 + xx; uint8_t sh = y & 7;
      *q &= ~(b << sh); if (sh > 3 && (y >> 3) < 7) q[128] &= ~(b >> (8 - sh));
    }
    return x + w + 1;
  }
  if (c == ' ') return x + 3;
  tiny(x, y, tinyIdx(c)); return x + 4;
}
uint8_t tinyAdv(char c) { return c == 'M' || c == 'W' ? 6 : c == 'N' ? 5 : c == ' ' ? 3 : 4; }
int16_t tinyW(PGM_P s) { int16_t w = 0; for (char c; (c = pgm_read_byte(s++)); ) w += tinyAdv(c); return w - 1; }   // width in pixels
int16_t tinyStr(int16_t x, int16_t y, PGM_P s) {
  for (char c; (c = pgm_read_byte(s++)); ) x = tinyChar(x, y, c);
  return x;
}
int16_t tinyNum(int16_t x, int16_t y, uint16_t v) { char b[6]; uint8_t n = 0; do { b[n++] = v % 10; v /= 10; } while (v); while (n) { tiny(x, y, b[--n]); x += 4; } return x; }
void frect(int16_t x, int16_t y, int16_t w, int16_t h, uint8_t col) { ab.fillRect(x, y, w, h, col); }   // (much faster than pixel by pixel)

// ---------------------------------------------------------------- music: Oh! Susanna (Stephen Foster, 1848, public domain)
const uint16_t SONG[] PROGMEM = {
  NOTE_G4,150, NOTE_A4,150, NOTE_B4,300, NOTE_D5,300, NOTE_D5,450, NOTE_E5,150, NOTE_D5,300, NOTE_B4,300,
  NOTE_G4,450, NOTE_A4,150, NOTE_B4,300, NOTE_B4,300, NOTE_A4,300, NOTE_G4,300, NOTE_A4,900, NOTE_REST,300,
  NOTE_G4,150, NOTE_A4,150, NOTE_B4,300, NOTE_D5,300, NOTE_D5,450, NOTE_E5,150, NOTE_D5,300, NOTE_B4,300,
  NOTE_G4,450, NOTE_A4,150, NOTE_B4,300, NOTE_B4,300, NOTE_A4,300, NOTE_A4,300, NOTE_G4,900, NOTE_REST,300,
  NOTE_C5,600, NOTE_E5,300, NOTE_E5,600, NOTE_REST,300, NOTE_D5,300, NOTE_D5,300, NOTE_B4,300, NOTE_G4,300,
  NOTE_A4,900, NOTE_REST,300, NOTE_G4,150, NOTE_A4,150, NOTE_B4,300, NOTE_D5,300, NOTE_D5,450, NOTE_E5,150,
  NOTE_D5,300, NOTE_B4,300, NOTE_G4,450, NOTE_A4,150, NOTE_B4,300, NOTE_B4,300, NOTE_A4,300, NOTE_A4,300,
  NOTE_G4,900, NOTE_REST,600,
  TONES_END };

// ---------------------------------------------------------------- game state
enum { S_TITLE, S_SOUND, S_CTRL, S_READY, S_RIDE, S_THROWN, S_BUCKO, S_SCORE };
uint8_t st = S_TITLE; uint16_t tick;
// the bull: frame 0 stand, 1 snort, then 4 frames for each buck (wind-up, halfway, key, flail): rear, kick, lunge, drop, leap, spin
uint8_t anim, step, hold, holdT;                 // anim 0 = idle, 1..5 = a buck; step 0..5 through its frames
uint8_t bullFrame() {
  if (!anim) return (tick >> 5) & 1;                                    // idle: stand / snort
  static const uint8_t SEQ[6] = { 0, 1, 2, 3, 2, 1 };                   // wind-up, halfway, key, flail, key, halfway
  return 2 + (anim - 1) * 4 + SEQ[step];
}
// the ride
uint16_t rideT;                                  // frames on the bull
uint8_t prompt = 255, spot = 255, pLeft, pWin, gap; // prompt 0..5 = up down left right inner outer
uint8_t slip, streak;                            // slip = strikes (3 and you're off)
uint16_t scoreV, best, hits, tries, cleanT; uint32_t rtSum; bool newRec;   // rtSum: total reaction time in milliseconds
// reaction timing, to the millisecond: the clock starts when the prompt actually reaches the screen, and the buttons
// are checked every millisecond between frames, so a press is timed when it happens, not at the next frame
uint32_t shownMs, pressMs; uint16_t winMs; uint8_t pressRaw, lastRaw; bool fresh;
void watchButtons() {
  uint8_t b = ab.buttonsState(), down = b & ~lastRaw; lastRaw = b;
  if (st == S_RIDE && prompt != 255 && !fresh && !pressRaw && down) { pressMs = millis(); pressRaw = down; }
}
uint8_t popT, popX, popY, popV, msgT, strikeT, shakeT, page, talkT; PGM_P msg; PGM_P talk;   // talk: what the bull is saying
void say(PGM_P m) { msg = m; msgT = 70; }
// the throw
float tx, ty, tvx, tvy, hx, hy, hvx, hvy; uint8_t landed, kicked;
const uint8_t BTN[6] = { UP_BUTTON, DOWN_BUTTON, LEFT_BUTTON, RIGHT_BUTTON, A_BUTTON, B_BUTTON };
const uint8_t BUCK[6] = { 1, 2, 3, 4, 5, 6 };    // which buck each button sets off: rear, kick, lunge, drop, leap (B, inner), spin (A, outer)

uint8_t windowFrames() {                         // time to react: 1.3 s at the start, 0.75 s at 20 s, 0.45 s at 40 s, never under 0.3 s
  float w = 78; for (uint16_t s = rideT / 60; s; s--) { w *= 0.9729f; if (w < 18) return 18; }
  return (uint8_t)w;
}
void startBuck(uint8_t a) { anim = a; step = 0; hold = max(2, pWin / 14); holdT = hold; snd.tone(90, 30); }
void newPrompt() {
  uint8_t s; do s = random(sizeof(SPOTS) / 2); while (s == spot);
  spot = s; prompt = random(6); pWin = pLeft = windowFrames(); winMs = (uint16_t)pWin * 50 / 3; tries++;
  fresh = true; pressRaw = 0; lastRaw = ab.buttonsState();      // a button already held down doesn't count
}
void slipped(bool wrong) {
  slip++; streak = 0; cleanT = 0; strikeT = 40; shakeT = 8; snd.tone(NOTE_E4, 60, NOTE_C4, 90);
  say(wrong ? PSTR("WRONG ONE!") : PSTR("TOO SLOW!"));
  if (slip >= 3) {                               // bucked off!
    uint8_t f = bullFrame(); int16_t sx = (int8_t)pgm_read_byte(&SEAT[f][0]), sy = (int8_t)pgm_read_byte(&SEAT[f][1]);
    tx = sx - 22; ty = sy - 26; tvx = -0.5f; tvy = -1.8f; hx = sx; hy = sy - 22; hvx = 1.2f; hvy = -3.8f; landed = kicked = 0; anim = 0;
    st = S_THROWN; tick = 0; prompt = 255;
    snd.tone(NOTE_G5, 80, NOTE_D5, 80, NOTE_G4, 160);
  }
}
// high score save: 'B' 'O' tag, the score, and a check byte, so data another game left there is never mistaken for a score
#define SAVE ((uint8_t*)404)
uint8_t saveCheck(uint16_t v) { return (v & 255) ^ (v >> 8) ^ 0xB0; }
uint16_t loadBest() {
  uint16_t v = eeprom_read_word((uint16_t*)(SAVE + 2));
  return (eeprom_read_byte(SAVE) == 'B' && eeprom_read_byte(SAVE + 1) == 'O' && eeprom_read_byte(SAVE + 4) == saveCheck(v)) ? v : 0;
}
void saveBest(uint16_t v) {
  eeprom_update_byte(SAVE, 'B'); eeprom_update_byte(SAVE + 1, 'O'); eeprom_update_word((uint16_t*)(SAVE + 2), v); eeprom_update_byte(SAVE + 4, saveCheck(v));
}
void startRide() { talkT = 0; rideT = 0; slip = streak = 0; scoreV = hits = tries = cleanT = 0; rtSum = 0; popT = msgT = strikeT = 0; anim = 0; prompt = 255; gap = 40; spot = 255; st = S_READY; tick = 0; }

// ---------------------------------------------------------------- drawing
// on the spin he reaches up (elbow bent), lifts his hat off, waves it high, lowers it, and puts it back on
// returns 0 = normal, else 1 + pose (0 grab, 1 lift, 2 wave)
uint8_t hatPose() { static const uint8_t P[6] = { 1, 2, 3, 3, 2, 1 }; return anim == 6 ? P[step] : 0; }
void riderBitmap(int16_t x, int16_t y, int16_t k) {
  uint8_t h = hatPose();
  if (h) FX::drawBitmap(x, y, FX_RIDERW, (h - 1) * N_LEAN + k, dbmMasked); else FX::drawBitmap(x, y, FX_RIDER, k, dbmMasked);
}
void drawRider(int8_t extraLean, int8_t dx) {
  uint8_t f = bullFrame();
  int16_t sx = (int8_t)pgm_read_byte(&SEAT[f][0]), sy = (int8_t)pgm_read_byte(&SEAT[f][1]);
  int16_t lean = (int8_t)pgm_read_byte(&SEAT[f][2]) + extraLean;
  int16_t k = (lean - LEAN0 + 4) / 8; if (k < 0) k = 0; if (k >= N_LEAN) k = N_LEAN - 1;
  riderBitmap(sx - RIDER_SX + dx, sy - RIDER_SY, k);
}
void drawScene(bool rider) {
  FX::drawBitmap(0, 0, FX_FENCE, 0, dbmNormal);
  FX::drawBitmap(0, 0, FX_BULL, bullFrame(), dbmMasked);
  if (rider) drawRider(-12 * slip + (anim ? 0 : ((tick >> 4) & 1) * 4), -2 * slip);   // slipping: leans back and slides off
}
void bigX(int16_t x, int16_t y, uint8_t n, uint8_t col) {   // an X, n pixels across, 2 px thick
  ab.drawLine(x, y, x + n - 1, y + n - 1, col); ab.drawLine(x + 1, y, x + n - 1, y + n - 2, col);
  ab.drawLine(x + n - 1, y, x, y + n - 1, col); ab.drawLine(x + n - 2, y, x, y + n - 2, col);
}
void hud() {
  // strikes, top left: three boxes, an X in each one you've used
  for (uint8_t i = 0; i < 3; i++) { frect(1 + i * 10, 1, 10, 10, WHITE); ab.drawRect(2 + i * 10, 2, 8, 8, BLACK); if (i < slip) bigX(3 + i * 10, 3, 6, BLACK); }
  // a big X flashes at the top when you get a strike
  if (strikeT) { strikeT--; if (strikeT & 4) { for (int8_t d = -1; d <= 1; d++) { bigX(55 + d, 2, 17, WHITE); bigX(55, 2 + d, 17, WHITE); } bigX(56, 3, 15, BLACK); } }
  // time (bottom left), score (bottom right), a message in between
  { uint16_t t = rideT / 6; frect(0, 55, 27, 9, WHITE); int16_t x = tinyNum(2, 57, t / 10); tiny(x, 57, 39); x = tinyNum(x + 4, 57, t % 10); tiny(x, 57, 28); }   // small timer
  { uint16_t v = scoreV; uint8_t n = 1; while (v >= 10) { v /= 10; n++; } frect(123 - n * 6, 54, n * 6 + 5, 10, WHITE); at(126 - n * 6, 55); pn(scoreV); }
  if (msgT) { msgT--; int16_t w = tinyW(msg) + 1; frect(64 - w / 2 - 2, 55, w + 3, 9, WHITE); tinyStr(64 - w / 2, 57, msg); }
  // points for the last hit float up from where the prompt was
  if (popT) { popT--; int16_t y = popY - (30 - popT) / 3; int16_t e = tinyStr(popX, y, PSTR("+")); tinyNum(e, y, popV); }
}
// the bull's speech bubble, up and to the right of his head, tail pointing down at him; one or two lines
void bullBubble() {
  if (!talkT) return; talkT--;
  PGM_P l2 = talk + strlen_P(talk) + 1;                      // second line follows the first in the same string
  uint8_t n1 = strlen_P(talk), n2 = pgm_read_byte(l2) ? strlen_P(l2) : 0, n = max(n1, n2);
  int16_t w1 = tinyW(talk), w2 = n2 ? tinyW(l2) : 0, wm = max(w1, w2);
  int16_t w = n2 ? wm + 8 : n * 6 + 7, h = n2 ? 18 : 12, x = min(124 - w, 92), y = 3;   // one short line: the bigger font
  ab.fillRoundRect(x - 1, y - 1, w + 2, h + 2, 4, WHITE); ab.drawRoundRect(x, y, w, h, 3, BLACK);
  for (uint8_t i = 0; i < 5; i++) ab.drawFastHLine(x + 6 - i / 2, y + h - 1 + i, 4 - i * 4 / 5 + 1, i ? BLACK : WHITE);   // tail
  ab.drawPixel(x + 6, y + h - 1, WHITE); ab.drawPixel(x + 7, y + h - 1, WHITE);
  if (n2) { tinyStr(x + 4 + (wm - w1) / 2, y + 3, talk); tinyStr(x + 4 + (wm - w2) / 2, y + 10, l2); }
  else { at(x + 4, y + 3); pp(talk); at(x + 5, y + 3); pp(talk); }
}
void drawPrompt() {
  if (prompt == 255) return;
  if (pLeft < pWin / 4 && (tick & 2)) return;    // blinks when time's nearly up
  FX::drawBitmap(pgm_read_byte(&SPOTS[spot][0]), pgm_read_byte(&SPOTS[spot][1]), FX_PROMPT, prompt, dbmMasked);
}

// ---------------------------------------------------------------- screens
void title() {
  uint8_t b = tick & 255;                          // the bull stares... blinks now and then... snorts
  uint8_t f = 0;
  if (b < 48) f = 4 + ((b >> 3) & 1);                   // grinds its teeth side to side
  else if (b > 90 && b < 97) f = 2;                     // blink
  else if (b > 130 && b < 160) f = 4 + ((b >> 2) & 1);  // faster grinding, getting mad...
  else if (b > 180 && b < 204) { f = 3; if (b == 181) shakeT = 10; }   // ...snorts and bellows (the screen shakes)
  FX::drawBitmap(0, 0, FX_TITLE, f, dbmNormal);
  if (((tick >> 5) & 1) && f != 3) tinyStr(64 - tinyW(PSTR("PRESS ANY BUTTON")) / 2, 57, PSTR("PRESS ANY BUTTON"));       // centred; hidden while his jaw drops
  if (ab.justPressed(A_BUTTON | B_BUTTON | UP_BUTTON | DOWN_BUTTON | LEFT_BUTTON | RIGHT_BUTTON)) { st = S_SOUND; tick = 0; snd.noTone(); }
}
void soundScreen() {
  bool on = ab.audio.enabled();
  ab.fillScreen(WHITE);                                                   // plain white, no ground line here
  // ON: the bull bucks for real and the cowboy rides it out; OFF: both asleep, the cowboy slumped over the bull's neck
  static uint8_t pause;
  if (on) {
    if (anim) { if (!--holdT) { holdT = hold; if (++step > 5) { anim = 0; pause = 18; } } }
    else if (pause) pause--;
    else { static const uint8_t SHOW[5] = { 2, 3, 6, 4, 5 }; static uint8_t k; anim = SHOW[k++ % 5]; step = 0; hold = holdT = 5; }   // kick, lunge, spin, drop, leap
  } else anim = 0;
  uint16_t t = tick; if (!on) tick = 0;                                   // asleep: hold still
  int8_t ox = -28;
  uint8_t f = bullFrame();
  FX::drawBitmap(ox, 0, FX_BULL, f, dbmMasked);
  { int16_t sx = (int8_t)pgm_read_byte(&SEAT[f][0]), sy = (int8_t)pgm_read_byte(&SEAT[f][1]);
    int16_t lean = on ? (int8_t)pgm_read_byte(&SEAT[f][2]) + (anim ? 0 : ((t >> 4) & 1) * 8) : 40;   // riding / slumped forward
    int16_t k = (lean - LEAN0 + 4) / 8; if (k < 0) k = 0; if (k >= N_LEAN) k = N_LEAN - 1;
    riderBitmap(sx - RIDER_SX + ox, sy - RIDER_SY + (on ? 0 : 2), k); }
  tick = t;
  frect(82, 0, 46, 64, WHITE);
  boldC(105, 2, PSTR("SOUND"));
  int8_t bob = (tick >> 4) & 1;
  at(103, 13 - bob); pc('\x18'); at(103, 31 + bob); pc('\x19');
  boldC(106, 22, on ? PSTR("ON") : PSTR("OFF"));
  FX::drawBitmap(82, 41, FX_SNDW, !on, dbmMasked);
  if (!on) { uint8_t z = (tick >> 3) & 15; at(68 + z / 2, 16 - z / 2); pc('Z'); if (z > 7) { at(66 + (z - 8) / 2, 18 - (z - 8) / 2); pc('z' - 32); } }   // Zs drifting up
  if (ab.justPressed(UP_BUTTON) || ab.justPressed(DOWN_BUTTON)) {
    ab.audio.toggle(); ab.audio.saveOnOff(); if (ab.audio.enabled()) snd.tone(NOTE_G5, 80, NOTE_D6, 120); else snd.noTone();
  }
  if (ab.justPressed(B_BUTTON)) { st = S_BUCKO; tick = 0; page = 0; snd.noTone(); }   // on to the old cowboy
  if (ab.justPressed(A_BUTTON)) { st = S_TITLE; tick = 0; }
}
void controls() {
  FX::drawBitmap(0, 0, FX_CTRL, (tick / 90) & 1, dbmNormal);
  if (tick > 15 && ab.justPressed(A_BUTTON | B_BUTTON | UP_BUTTON | DOWN_BUTTON | LEFT_BUTTON | RIGHT_BUTTON)) { snd.noTone(); startRide(); }
}
void outlined(int16_t cx, int16_t y, PGM_P s) {   // bold black text with a white edge, no box
  tw_ = true;
  for (int8_t dy = -1; dy <= 1; dy++) for (int8_t dx = -1; dx <= 1; dx++) if (dx || dy) boldC(cx + dx, y + dy, s);
  tw_ = false; boldC(cx, y, s);
}
void ready() {                                   // 3, 2, 1, GO! in the open sky behind the bull
  drawScene(true);
  uint8_t n = tick / 40;
  static const char NUM[] PROGMEM = "3\0" "2\0" "1\0" "GO!";
  if (n < 4) outlined(22, 12, NUM + n * 2);
  if (tick % 40 == 0 && n < 4) snd.tone(n < 3 ? NOTE_C5 : NOTE_C6, n < 3 ? 80 : 200);
  if (tick >= 170) { st = S_RIDE; tick = 0; gap = 20; }
}
void ride() {
  rideT++;
  // the bull: bucking, or idle while a prompt is up
  if (anim) {
    if (!--holdT) { holdT = hold; if (++step > 5) { anim = 0; gap = max(4, pWin / 4); } else if (step == 3) snd.tone(70, 40); }
  } else if (prompt == 255) {
    if (gap) gap--; else newPrompt();
  } else if (!fresh) {                          // (the frame the prompt is drawn, the clock hasn't started yet)
    uint32_t now = millis();
    uint8_t pressed = 0;                         // 1..6 = which button, if one went down
    if (pressRaw) { for (uint8_t i = 0; i < 6; i++) if (pressRaw & BTN[i]) { pressed = i + 1; if (i == prompt) break; } }
    uint16_t rt = pressRaw ? (uint16_t)(pressMs - shownMs) : (uint16_t)min(now - shownMs, (uint32_t)60000);
    pLeft = rt >= winMs ? 0 : (uint8_t)((uint32_t)(winMs - rt) * 3 / 50);    // frames left, for the blink when time's nearly up
    if (pressed && rt >= winMs) pressed = 0;     // pressed after the time ran out: that's too slow
    if (pressed == prompt + 1) {                 // got it: the bull bucks the way you pushed
      snd.tone(NOTE_A5, 25, NOTE_E6, 35);
      // points: 10 for hitting it, up to 90 more for how much of the time you had left (to the millisecond, rounded)
      uint8_t pts = 10 + ((uint32_t)90 * (winMs - rt) + winMs / 2) / winMs; scoreV += pts; hits++; rtSum += rt;
      popV = pts; popT = 30; popX = pgm_read_byte(&SPOTS[spot][0]) + 4; popY = pgm_read_byte(&SPOTS[spot][1]) + 8;
      startBuck(BUCK[prompt]); prompt = 255;
      if (++streak >= 8 && slip) { slip--; streak = 0; say(PSTR("BACK ON!")); talkT = 0; }    // eight in a row: he pulls himself back up
      else if (streak % 5 == 0) {
        static const char C0[] PROGMEM = "YEEHAW!", C1[] PROGMEM = "HANG ON!", C2[] PROGMEM = "GIDDY UP!", C3[] PROGMEM = "RIDE EM!", C4[] PROGMEM = "WHOA NELLY!";
        static PGM_P const CALLS[5] PROGMEM = { C0, C1, C2, C3, C4 };
        say((PGM_P)pgm_read_ptr(&CALLS[random(5)]));
      }
    } else if (pressed || rt >= winMs) {        // wrong button, or too slow: a strike, and the bull bucks anyway
      prompt = 255; slipped(pressed != 0);
      if (st == S_RIDE) startBuck(1 + random(6));
    }
  }
  if (++cleanT >= 420) { cleanT = 0; scoreV += 250; say(PSTR("CLEAN 7S +250")); snd.tone(NOTE_C6, 60, NOTE_G6, 120); }   // 7 seconds without a strike
  drawScene(true); bullBubble(); drawPrompt(); hud();
}
void thrown() {
  // he's thrown straight up... the bull waits for him to come down... and kicks him clean off the screen
  if (anim) { if (!--holdT) { holdT = hold; if (++step > 5) anim = 0; } }
  if (!kicked) {
    if (tvy > 0.2f && !anim) { anim = 2; step = 0; hold = holdT = 4; snd.tone(90, 30); }   // heels coming up
    if (anim == 2 && step == 2) {                                                         // WHAM
      kicked = 1; tvx = -3.0f; tvy = -1.5f; snd.tone(NOTE_C3, 40, NOTE_C2, 140); say(PSTR("OOF!")); strikeT = 0; shakeT = 16; talk = PSTR("LOL\0"); talkT = 255;
    }
  }
  tvy += kicked ? 0.04f : 0.12f; tx += tvx; ty += tvy;
  drawScene(false);
  hvy += 0.12f; hx += hvx; hy += hvy; if (hy > 60) { hy = 60; hvx = hvy = 0; }
  if (tx > -44) FX::drawBitmap((int16_t)tx, (int16_t)ty, FX_TUMBLE, (tick >> (kicked ? 1 : 2)) & 7, dbmMasked);
  FX::drawBitmap((int16_t)hx, (int16_t)hy, FX_HAT, 0, dbmMasked);
  bullBubble(); hud();
  if (kicked) kicked++;
  if (kicked > 80) {                                         // (time to enjoy the bull laughing)
    newRec = scoreV > best;
    if (newRec) { best = scoreV; saveBest(best); }
    st = S_SCORE; tick = 0;
    if (newRec) snd.tone(NOTE_C5, 90, NOTE_E5, 90, NOTE_G5, 220); else snd.tone(NOTE_G4, 160, NOTE_E4, 160, NOTE_C4, 320);
  }
}

// one line of text built in RAM, then drawn centred in the normal 5x7 font
char lb[24]; uint8_t ln;
void lbC(char c) { if (ln < 23) { lb[ln++] = c; lb[ln] = 0; } }
void lbS(PGM_P t) { char c; while ((c = pgm_read_byte(t++))) lbC(c); }
void lbN(uint16_t v) { char b[6]; uint8_t n = 0; do { b[n++] = '0' + v % 10; v /= 10; } while (v); while (n) lbC(b[--n]); }
void lineC(uint8_t y, bool bold) {
  int16_t x = 64 - (ln * 6 - 1 + bold) / 2;
  for (uint8_t k = 0; k <= bold; k++) { at(x + k, y); for (uint8_t i = 0; i < ln; i++) pc(lb[i]); }
  ln = 0;
}
// a score line: small label then the value (in lb) in the normal font, centred together
void mixRow(uint8_t y, PGM_P label) {
  uint8_t vw = 0; for (uint8_t i = 0; i < ln; i++) vw += lb[i] == 's' ? 5 : 6;
  int16_t w = tinyW(label) + 4 + vw, x = 64 - w / 2;
  x = tinyStr(x, y + 2, label) + 4;
  at(x, y); for (uint8_t i = 0; i < ln; i++) { char c = lb[i]; if (c == 's') { tiny(tx_ + 1, y + 2, 28); tx_ += 5; } else pc(c); }   // 's' = a small S for seconds
  ln = 0;
}
// the old cowboy, between the sound screen and the controls: a speech bubble that types itself out, a page at a time
const char K0[] PROGMEM = "HOWDY, BUCKO!"; const char K1[] PROGMEM = "MEET BUCKY"; const char K2[] PROGMEM = "THE BULL,"; const char K3[] PROGMEM = "MEANEST"; const char K4[] PROGMEM = "BUCKER IN"; const char K4b[] PROGMEM = "THE WEST.";
const char K5[] PROGMEM = "PRESS FAST OR"; const char K6[] PROGMEM = "GET BUCKED."; const char K7[] PROGMEM = "AND REMEMBER,"; const char K8[] PROGMEM = "DON'T TAKE"; const char K9[] PROGMEM = "ANY BULL!";
const char* const KL[] PROGMEM = { K0, K1, K2, K3, K4, K4b, K5, K6, K7, K8, K9 };
const uint8_t KPAGE[3] PROGMEM = { 0, 6, 11 };               // first line of each page (two speech bubbles)
void bucko() {
  uint8_t a = pgm_read_byte(&KPAGE[page]), b = pgm_read_byte(&KPAGE[page + 1]);
  uint8_t shown = tick < 750 ? tick / 3 : 250, n = 0;        // letters typed so far on this page (capped so it can't wrap round)
  uint8_t total = 0; for (uint8_t l = a; l < b; l++) total += strlen_P((PGM_P)pgm_read_ptr(&KL[l]));
  FX::drawBitmap(0, 0, FX_COWBOY, shown < total ? (tick >> 2) & 3 : 3, dbmNormal);   // jaw flapping and swaying while he talks
  uint8_t y0 = 29 - (b - a) * 7 / 2;                         // the page's lines centred in the bubble, 7 px apart
  for (uint8_t l = a; l < b; l++) {
    PGM_P t = (PGM_P)pgm_read_ptr(&KL[l]); uint8_t len = strlen_P(t);
    int16_t x = 95 - tinyW(t) / 2, y = y0 + (l - a) * 7;
    for (uint8_t k = 0; k < len; k++) {
      if (n++ >= shown) break;
      x = tinyChar(x, y, pgm_read_byte(t + k));
    }
  }
  bool done = shown >= n;
  if (!done && (tick % 3) == 0) snd.tone(220 + (tick & 7) * 30, 12);   // mumbling as he talks
  if (done && ((tick >> 4) & 1)) { tiny(116, 47, 37); for (uint8_t i = 0; i < 3; i++) ab.drawFastHLine(116 + i, 46 + i, 5 - 2 * i, BLACK); }   // little arrow: more
  if (ab.justPressed(A_BUTTON | B_BUTTON)) {
    if (!done) tick = 200;                                   // finish the page
    else if (++page >= 2) { st = S_CTRL; tick = 0; } else tick = 0;
  }
}
void arrowL(int16_t x, int16_t y) { for (uint8_t i = 0; i < 3; i++) ab.drawFastVLine(x + i, y + 2 - i, 1 + 2 * i, BLACK); }   // small solid arrows
void arrowR(int16_t x, int16_t y) { for (uint8_t i = 0; i < 3; i++) ab.drawFastVLine(x + 2 - i, y + 2 - i, 1 + 2 * i, BLACK); }
void score() {
  frect(0, 0, 128, 64, WHITE);
  frect(2, 2, 124, 10, BLACK); tw_ = 1; lbS(PSTR("SCORE ")); lbN(scoreV); lineC(3, 0); tw_ = 0;     // white on a thin black band
  static const uint16_t AT[13] PROGMEM = { 100, 250, 450, 700, 1000, 1350, 1750, 2200, 2700, 3300, 4000, 4800, 6000 };
  uint8_t r = 0; while (r < 13 && scoreV >= pgm_read_word(&AT[r])) r++;
  tinyStr(64 - tinyW(PSTR("YOUR RANK")) / 2, 14, PSTR("YOUR RANK"));
  FX::drawBitmap(4, 19, FX_RANKS, r, dbmMasked);                                // the rank, big and bold (names are in art/fxpack.py)
  { uint16_t t = rideT / 6; lbN(t / 10); lbC('.'); lbN(t % 10); lbC('s'); mixRow(33, PSTR("TIME BUCKING")); }
  { uint16_t a = hits ? (rtSum + hits / 2) / hits : 0;          // average reaction in milliseconds, shown as 0.573 seconds
    lbN(a / 1000); lbC('.'); if (a % 1000 < 100) lbC('0'); if (a % 1000 < 10) lbC('0'); lbN(a % 1000); lbC('s'); mixRow(41, PSTR("AVERAGE REACTION TIME")); }
  if (!newRec || (tick & 16)) { lbN(best); mixRow(49, newRec ? PSTR("NEW HIGH SCORE") : PSTR("HIGH SCORE")); }   // flashes on a new record
  arrowL(3, 57); tinyStr(8, 57, PSTR("TITLE"));                                   // left arrow: title
  tinyStr(120 - tinyW(PSTR("PLAY AGAIN")), 57, PSTR("PLAY AGAIN")); arrowR(122, 57);                           // right arrow: ride again
  if (tick > 30) {
    if (ab.justPressed(RIGHT_BUTTON)) startRide();
    if (ab.justPressed(LEFT_BUTTON)) { st = S_TITLE; tick = 0; }
  }
}

void setup() {
  ab.boot(); ab.display(); FX::begin(FX_DATA_PAGE); ab.systemButtons(); ab.audio.begin(); ab.waitNoButtons();
  ab.setFrameRate(60);
  randomSeed(ab.generateRandomSeed());
  best = loadBest();
}
void loop() {
  if (!ab.nextFrame()) { watchButtons(); return; }   // between frames: watch the buttons every millisecond
  watchButtons(); ab.pollButtons(); tick++;
  ab.clear();
  switch (st) {
    case S_TITLE: title(); break;
    case S_SOUND: soundScreen(); break;
    case S_CTRL: controls(); break;
    case S_READY: ready(); break;
    case S_RIDE: ride(); break;
    case S_THROWN: thrown(); break;
    case S_BUCKO: bucko(); break;
    case S_SCORE: score(); break;
  }
  if (st == S_TITLE || st == S_CTRL) { if (!snd.playing()) snd.tones(SONG); }   // music on the title and controls (not the sound screen)
  if (shakeT) {                                    // screen shake: slide the whole picture a pixel or two sideways
    shakeT--; int8_t d = (shakeT & 2) ? 2 : -2; if (shakeT < 4) d /= 2;
    for (uint8_t p = 0; p < 8; p++) {
      uint8_t* row = ab.sBuffer + p * 128;
      if (d > 0) { memmove(row + d, row, 128 - d); memset(row, 0xFF, d); } else { memmove(row, row - d, 128 + d); memset(row + 128 + d, 0xFF, -d); }
    }
  }
  FX::display();
  if (fresh && st == S_RIDE) { shownMs = millis(); fresh = false; }   // the prompt is on the screen now: start the clock
}
