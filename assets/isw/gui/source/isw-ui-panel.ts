import { createIcon, hasIcon } from './icons';

export interface PanelTab {
  id: string;
  label: string;
  disabled?: boolean;
  disabledReason?: string;
  badge?: number | string;
}

export interface PanelProps {
  title: string;
  icon?: string;
  iconId?: string;
  tabs?: PanelTab[];
  activeTabId?: string;
  onSelectTab?: (id: string) => void;
  onClose?: () => void;
  closeLabel?: string;
  footer?: string | HTMLElement;
  children?: Array<Node | string>;
  bodyMaxHeight?: number;
  scrollable?: boolean;
}

let plateSeq = 0;

export function createPanel(props: PanelProps): HTMLElement {
  const root = document.createElement('section');
  root.className = 'isw-ui isw-ui-panel';
  root.setAttribute('aria-label', props.title);

  const bar = document.createElement('header');
  bar.className = 'isw-ui-panel__bar';

  if (props.iconId && hasIcon(props.iconId)) {
    const box = document.createElement('span');
    box.className = 'isw-ui-panel__icon';
    box.append(createIcon(props.iconId, { size: 24 }));
    bar.append(box);
  } else if (props.icon) {
    const icon = document.createElement('span');
    icon.className = 'isw-ui-panel__icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = props.icon;
    bar.append(icon);
  }

  const title = document.createElement('h3');
  title.className = 'isw-ui-panel__title';
  title.textContent = props.title;
  bar.append(title);

  const close = document.createElement('button');
  close.type = 'button';
  close.className = 'isw-ui-panel__close';
  close.setAttribute('aria-label', props.closeLabel ?? 'Close');
  close.append(createIcon('misc.close', { size: 14, family: 'menu' }));
  if (props.onClose) {
    close.addEventListener('click', () => props.onClose?.());
    bar.append(close);
  }
  root.append(bar);

  if (props.tabs && props.tabs.length > 0) {
    const strip = document.createElement('div');
    strip.className = 'isw-ui-panel__tabs';
    strip.setAttribute('role', 'tablist');
    for (const tab of props.tabs) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'isw-ui-tab';
      button.setAttribute('role', 'tab');
      button.dataset.tab = tab.id;
      const label = document.createElement('span');
      label.textContent = tab.label;
      button.append(label);
      const active = tab.id === props.activeTabId;
      button.setAttribute('aria-selected', String(active));
      button.classList.toggle('isw-ui-tab--active', active);
      if (tab.badge !== undefined) {
        const badge = document.createElement('span');
        badge.className = 'isw-ui-tab__badge';
        badge.textContent = String(tab.badge);
        badge.setAttribute('aria-hidden', 'true');
        button.append(badge);
        button.setAttribute('aria-label', `${tab.label}, ${tab.badge} waiting`);
      }
      if (tab.disabled) {
        // Refused tabs stay focusable (aria-disabled, never native disabled)
        // so keyboard and touch users can pin the reason on screen with
        // Enter or a tap (C2 visible change, C10 reason on demand). The
        // plate never shows permanently — the strip stays clean when the
        // tab is irrelevant — but it is always one press away.
        button.setAttribute('aria-disabled', 'true');
        button.classList.add('isw-ui-tab--disabled');
        button.title = tab.disabledReason ?? 'Unavailable right now';
        plateSeq += 1;
        const plate = document.createElement('span');
        plate.className = 'isw-ui-tab__plate';
        plate.id = `isw-panel-reason-${plateSeq}`;
        plate.setAttribute('role', 'tooltip');
        plate.textContent = tab.disabledReason ?? 'Unavailable right now';
        button.setAttribute('aria-describedby', plate.id);
        button.append(plate);
        button.addEventListener('click', () => {
          button.classList.toggle('isw-ui-tab--plate-open');
        });
      } else if (props.onSelectTab) {
        button.addEventListener('click', () => props.onSelectTab?.(tab.id));
      }
      strip.append(button);
    }
    root.append(strip);
  }

  const body = document.createElement('div');
  body.className = 'isw-ui-panel__body';

  const scroll = document.createElement('div');
  scroll.className = 'isw-ui-panel__scroll';
  scroll.style.overflowY = 'auto';
  if (props.bodyMaxHeight !== undefined) scroll.style.maxHeight = `${props.bodyMaxHeight}px`;
  for (const child of props.children ?? []) scroll.append(child);

  const scrollbar = document.createElement('span');
  scrollbar.className = 'isw-ui-panel__scrollbar';
  scrollbar.setAttribute('aria-hidden', 'true');
  const thumb = document.createElement('span');
  thumb.className = 'isw-ui-panel__scrollbar-thumb';
  scrollbar.append(thumb);

  const syncScrollbar = (): void => {
    const overflows = scroll.clientHeight > 0 && scroll.scrollHeight > scroll.clientHeight + 1;
    const show = overflows || (props.scrollable === true && scroll.clientHeight === 0);
    root.classList.toggle('isw-ui-panel--scrollable', show);
    if (!show) return;
    const ratio =
      scroll.clientHeight > 0 && scroll.scrollHeight > 0 ? scroll.clientHeight / scroll.scrollHeight : 0.45;
    const height = Math.round(Math.min(0.9, Math.max(0.18, ratio)) * 100);
    thumb.style.height = `${height}%`;
    const travel = scroll.scrollHeight - scroll.clientHeight;
    const progress = travel > 0 ? scroll.scrollTop / travel : 0;
    thumb.style.top = `${Math.round(progress * (100 - height))}%`;
  };
  if (props.scrollable === true) root.classList.add('isw-ui-panel--scrollable');
  body.append(scroll, scrollbar);
  root.append(body);
  scroll.addEventListener('scroll', syncScrollbar);
  if (typeof requestAnimationFrame === 'function') requestAnimationFrame(syncScrollbar);

  if (props.footer !== undefined) {
    const footer = document.createElement('footer');
    footer.className = 'isw-ui-panel__footer';
    if (typeof props.footer === 'string') footer.textContent = props.footer;
    else footer.append(props.footer);
    root.append(footer);
  }

  return root;
}
