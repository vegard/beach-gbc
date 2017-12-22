; rgbds code template from
; <http://assemblydigest.tumblr.com/post/77198211186/tutorial-making-an-empty-game-boy-rom-in-rgbds>

SECTION "rom", ROM0

; $0000 - $003F: RST handlers.
ret
REPT 7
    nop
ENDR
; $0008
ret
REPT 7
    nop
ENDR
; $0010
ret
REPT 7
    nop
ENDR
; $0018
ret
REPT 7
    nop
ENDR
; $0020
ret
REPT 7
    nop
ENDR
; $0028
ret
REPT 7
    nop
ENDR
; $0030
ret
REPT 7
    nop
ENDR
; $0038
ret
REPT 7
    nop
ENDR

; $0040 - $0067: Interrupt handlers.
jp draw
REPT 5
    nop
ENDR
; $0048
jp stat
REPT 5
    nop
ENDR
; $0050
jp timer
REPT 5
    nop
ENDR
; $0058
jp serial
REPT 5
    nop
ENDR
; $0060
jp joypad
REPT 5
    nop
ENDR

; $0068 - $00FF: Free space.
DS $98

; $0100 - $0103: Startup handler.
nop
jp main

; $0104 - $0133: The Nintendo Logo.
DB $CE, $ED, $66, $66, $CC, $0D, $00, $0B
DB $03, $73, $00, $83, $00, $0C, $00, $0D
DB $00, $08, $11, $1F, $88, $89, $00, $0E
DB $DC, $CC, $6E, $E6, $DD, $DD, $D9, $99
DB $BB, $BB, $67, $63, $6E, $0E, $EC, $CC
DB $DD, $DC, $99, $9F, $BB, $B9, $33, $3E

; $0134 - $013E: The title, in upper-case letters, followed by zeroes.
DB "TEST"
DS 7 ; padding

; $013F - $0142: The manufacturer code.
DS 4

; $0143: Gameboy Color compatibility flag.    
GBC_UNSUPPORTED EQU $00
GBC_COMPATIBLE EQU $80
GBC_EXCLUSIVE EQU $C0
DB GBC_EXCLUSIVE

; $0144 - $0145: "New" Licensee Code, a two character name.
DB "OK"

; $0146: Super Gameboy compatibility flag.
SGB_UNSUPPORTED EQU $00
SGB_SUPPORTED EQU $03
DB SGB_UNSUPPORTED

; $0147: Cartridge type. Either no ROM or MBC5 is recommended.
CART_ROM_ONLY EQU $00
CART_MBC1 EQU $01
CART_MBC1_RAM EQU $02
CART_MBC1_RAM_BATTERY EQU $03
CART_MBC2 EQU $05
CART_MBC2_BATTERY EQU $06
CART_ROM_RAM EQU $08
CART_ROM_RAM_BATTERY EQU $09
CART_MMM01 EQU $0B
CART_MMM01_RAM EQU $0C
CART_MMM01_RAM_BATTERY EQU $0D
CART_MBC3_TIMER_BATTERY EQU $0F
CART_MBC3_TIMER_RAM_BATTERY EQU $10
CART_MBC3 EQU $11
CART_MBC3_RAM EQU $12
CART_MBC3_RAM_BATTERY EQU $13
CART_MBC4 EQU $15
CART_MBC4_RAM EQU $16
CART_MBC4_RAM_BATTERY EQU $17
CART_MBC5 EQU $19
CART_MBC5_RAM EQU $1A
CART_MBC5_RAM_BATTERY EQU $1B
CART_MBC5_RUMBLE EQU $1C
CART_MBC5_RUMBLE_RAM EQU $1D
CART_MBC5_RUMBLE_RAM_BATTERY EQU $1E
CART_POCKET_CAMERA EQU $FC
CART_BANDAI_TAMA5 EQU $FD
CART_HUC3 EQU $FE
CART_HUC1_RAM_BATTERY EQU $FF
DB CART_MBC5

; $0148: Rom size.
ROM_32K EQU $00
ROM_64K EQU $01
ROM_128K EQU $02
ROM_256K EQU $03
ROM_512K EQU $04
ROM_1024K EQU $05
ROM_2048K EQU $06
ROM_4096K EQU $07
ROM_1152K EQU $52
ROM_1280K EQU $53
ROM_1536K EQU $54
DB ROM_32K

; $0149: Ram size.
RAM_NONE EQU $00
RAM_2K EQU $01
RAM_8K EQU $02
RAM_32K EQU $03
DB RAM_NONE

; $014A: Destination code.
DEST_JAPAN EQU $00
DEST_INTERNATIONAL EQU $01
DB DEST_INTERNATIONAL
; $014B: Old licensee code.
; $33 indicates new license code will be used.
; $33 must be used for SGB games.
DB $33
; $014C: ROM version number
DB $00
; $014D: Header checksum.
; Assembler needs to patch this.
DB $FF
; $014E- $014F: Global checksum.
; Assembler needs to patch this.
DW $FACE

; Helper macros
Breakpoint: MACRO
    ld b, b
ENDM

; TODO: use labels and let rgbds allocate addresses
frame_counter EQU $c000
current_frame EQU $c004

; $0150: Code!
main:
    ; we have to wait until LY (LCDC Y-coordinate) >= 144 to
    ; prevent hardware damage when disabling the LCD
.ly_loop:
    ldh a, [$44]
    cp 144
    jr c, .ly_loop

    ; disable LCD
    ld a, 0
    ldh [$40], a

    ; set CPU double speed (not that it will help us)
    ; 
    ;ld a, 1
    ;ldh [$4d], a
    ;stop

    ; initialize frame counter
    ld hl, frame_counter
    ld a, 0
    ld [hl], a

    ; initialize current frame
    ld hl, current_frame
    ld a, 0
    ld [hl], a

    ; set palette
    ld a, $80
    ldh [$68], a
    ld hl, palette
    ld c, (palette_end - palette)
.palette_loop:
    ld a, [hl]
    ldh [$69], a
    inc hl
    dec c
    jr nz, .palette_loop

    ; copy tiles into VRAM, bank 0
    ld a, 0
    ldh [$4f], a
    ld hl, tiles0
    ld de, $8000
    ld bc, (256 + tiles0_end - tiles0)
    call memcpy

    ; copy tiles, bank 1
    ld a, 1
    ldh [$4f], a
    ld hl, tiles1
    ld de, $8000
    ld bc, (256 + tiles1_end - tiles1)
    call memcpy

    ; copy initial map into VRAM
    ld a, 0
    ldh [$4f], a
    ld hl, frame_init_0
    ld de, $9800
    ld bc, (256 + frame_init_0_end - frame_init_0)
    call memcpy
    ld a, 1
    ldh [$4f], a
    ld hl, frame_init_1
    ld de, $9800
    ld bc, (256 + frame_init_1_end - frame_init_1)
    call memcpy

    ; set LCD scroll
    ld a, 16
    ldh [$42], a
    ld a, 0
    ldh [$43], a

    ; enable LCD
    ld a, $90
    ldh [$40], a

    ; enable vblank interrupts
    ldh a, [$ff]
    or $ff
    ldh [$ff], a
    ei

.halt_loop:
    ; wait for interrupt
    halt
    nop

    ; check for joypad events
    ld a, $20
    ldh [$00], a
    ldh a, [$00]
    ld b, a

.down:
    and a, $08
    jr nz, .down_done
    ldh a, [$42]
    cp 16
    jr nc, .down_done
    inc a
    ldh [$42], a
.down_done:
    ld a, b

.up:
    and a, $04
    jr nz, .up_done
    ldh a, [$42]
    cp 1
    jr c, .up_done
    dec a
    ldh [$42], a
.up_done:
    ld a, b

.left:
    and a, $02
    jr nz, .left_done
    ldh a, [$43]
    cp 1
    jr c, .left_done
    dec a
    ldh [$43], a
.left_done:
    ld a, b

.right:
    and a, $01
    jr nz, .right_done
    ldh a, [$43]
    cp 96
    jr nc, .right_done
    inc a
    ldh [$43], a
.right_done:

    jr .halt_loop

draw_next_frame:
    ; reset frame counter
    ld hl, frame_counter
    ld a, 0
    ld [hl], a

    ; scroll
    ;ldh a, [$42]
    ;inc a
    ;ldh [$42], a

    ; get frame counter, leave pointer to frame in de
    ld hl, current_frame
    ld a, [hl]
    add a, a
    ld b, 0
    ld c, a
    ld hl, frames
    add hl, bc

    ld e, [hl]
    inc hl
    ld d, [hl]

    ; call (de)
    ld hl, .done
    push hl
    push de
    ret

.done:
    ; increment frame counter
    ld hl, current_frame
    ld a, [hl]
    inc a
    cp 19 ; TODO: 18?
    jr c, .save_frame_counter
    ld a, 0
.save_frame_counter:
    ld [hl], a

    ret

memcpy:
.loop:
    ld a, [hl]
    ld [de], a
    inc hl
    inc de
    dec c ; assumes (bc > 0) initially
    jr nz, .loop
    dec b ; assumes (bc > 255) initially
    jr nz, .loop
    ret

map_init:
    ld hl, $0000
    ld de, $9800

    ret

draw:
    ; check if we should advance to the next frame
    ld hl, frame_counter
    ld a, [hl]
    inc a
    ld [hl], a
    cp 6
    jr c, .ret

    ; reset counter
    ld a, 0
    ld [hl], a

    call draw_next_frame

.ret:
    reti

stat:
    reti

timer:
    reti

serial:
    reti

joypad:

    reti

;
; data
;

INCLUDE "palette.asm"
INCLUDE "tiles-0.asm"
INCLUDE "tiles-1.asm"

SECTION "maps", ROMX
INCLUDE "maps.asm"
