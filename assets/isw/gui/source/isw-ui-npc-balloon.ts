// N2, the NPC speech balloon: the approved dialogue design from the shop /
// NPC mock (~/serve/isw-mocks/shop-npc/, variant N2: "Speech balloon over
// the NPC. APPROVED, choices under the text inside the balloon").
//
// The CH4 balloon family (speech-balloon.ts): the same gold tokens, a tail
// pointing down at the head. It holds the speaker's name, one line, and a
// row of choices under the line, numbered 1..n in the order given — the
// numbers are the keys that pick them. The host decides which choices an
// NPC offers and what each does; the balloon only draws them and reports
// a pick.
//
// Placement: the element is a zero-size anchor. The host puts it where the
// tail should touch — over the NPC's head; the balloon grows up from it.

export interface NpcBalloonChoice {
  id: string;
  label: string;
}

export interface NpcBalloonProps {
  name: string;
  line: string;
  /** In key order: the first is key 1 and is drawn as the primary (chrome) button. */
  choices: NpcBalloonChoice[];
  onChoose?: (id: string) => void;
}

export interface NpcBalloonShown {
  visible: boolean;
  name: string;
  line: string;
  choices: string[];
}

export interface NpcBalloon {
  element: HTMLElement;
  /** Draw (or redraw) and show. */
  show(props: NpcBalloonProps): void;
  hide(): void;
  /** Pick the choice on key `n` (1-based); false when there is none. */
  choose(n: number): boolean;
  shown(): NpcBalloonShown;
}

export function createNpcBalloon(): NpcBalloon {
  const root = document.createElement('div');
  root.className = 'isw-ui isw-ui-npcsay';
  root.hidden = true;
  let current: NpcBalloonProps | null = null;

  const pick = (id: string): void => current?.onChoose?.(id);

  return {
    element: root,
    show(props) {
      current = props;
      const balloon = document.createElement('div');
      balloon.className = 'isw-ui-npcsay__bal';
      balloon.setAttribute('role', 'dialog');
      balloon.setAttribute('aria-label', props.name);
      const who = document.createElement('div');
      who.className = 'isw-ui-npcsay__who';
      who.textContent = props.name;
      const line = document.createElement('p');
      line.className = 'isw-ui-npcsay__line';
      line.setAttribute('aria-live', 'polite');
      line.textContent = props.line;
      balloon.append(who, line);
      if (props.choices.length > 0) {
        const chips = document.createElement('div');
        chips.className = 'isw-ui-npcsay__chips';
        props.choices.forEach((choice, index) => {
          const button = document.createElement('button');
          button.type = 'button';
          button.className = index === 0 ? 'isw-ui-gbtn' : 'isw-ui-gbtn isw-ui-gbtn--ghost';
          button.dataset.choice = choice.id;
          button.setAttribute('aria-keyshortcuts', String(index + 1));
          const key = document.createElement('span');
          key.className = 'isw-ui-gbtn__k';
          key.setAttribute('aria-hidden', 'true');
          key.textContent = String(index + 1);
          button.append(key, choice.label);
          button.addEventListener('click', () => pick(choice.id));
          chips.append(button);
        });
        balloon.append(chips);
      }
      root.replaceChildren(balloon);
      root.hidden = false;
    },
    hide() {
      current = null;
      root.hidden = true;
      root.replaceChildren();
    },
    choose(n) {
      const choice = current?.choices[n - 1];
      if (!choice || root.hidden) return false;
      pick(choice.id);
      return true;
    },
    shown: () => ({
      visible: !root.hidden,
      name: current?.name ?? '',
      line: current?.line ?? '',
      choices: current?.choices.map((choice) => choice.label) ?? [],
    }),
  };
}
