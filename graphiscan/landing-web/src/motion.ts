import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
gsap.registerPlugin(ScrollTrigger);

let activeMedia: ReturnType<typeof gsap.matchMedia> | undefined;

// Never hide already-painted content when the motion module loads late.
function replayOnVisit(animation: gsap.core.Animation, trigger: Element, start = 'top 90%') {
  const bounds = trigger.getBoundingClientRect();
  animation.progress(bounds.bottom > 0 && bounds.top < innerHeight ? 1 : 0).pause();
  ScrollTrigger.create({ trigger, start, end: 'bottom top',
    onEnter: () => { animation.play(); }, onLeave: () => { animation.reverse(); },
    onEnterBack: () => { animation.play(); }, onLeaveBack: () => { animation.reverse(); },
  });
}

export function initializeMotion() {
  activeMedia?.revert();
  const media = gsap.matchMedia();
  activeMedia = media;
  media.add({ always: '(min-width: 0px)', reduced: '(prefers-reduced-motion: reduce)', narrow: '(max-width: 760px)' }, context => {
    if (context.conditions?.reduced) {
      gsap.set('main > section > .wrap, main > section, .hero h1 > span, .hero-kicker, .hero-description, .hero-link, .hero-media > img, .product-stage, .platform-heading, .understanding-intro h2, .faq h2, .workflow-tabs, .workflow-tabs > *, .dysgraphia-details > *, .role-content, .role-copy, #role-image, #workflow-image, #workflow-detail', { clearProps: 'opacity,transform' });
      return;
    }
    const intro = gsap.timeline({ paused: true, defaults: { ease: 'power3.out', immediateRender: false } })
      .fromTo('.hero h1 > span', { y: 0, yPercent: 32, opacity: .15 }, { y: 0, yPercent: 0, opacity: 1, duration: 1.15, stagger: .1 })
      .fromTo('.hero-kicker, .hero-description, .hero-link', { y: 14, opacity: 0 }, { y: 0, opacity: 1, duration: .75, stagger: .07 }, .35);
    const hero = document.querySelector('.hero');
    if (hero) {
      replayOnVisit(intro, hero, 'top bottom');
      replayOnVisit(gsap.fromTo('.hero-media > img', { scale: 1.06 }, { scale: 1, duration: 2.1, ease: 'power2.out', paused: true, immediateRender: false }), hero, 'top bottom');
    }

    // Trigger on the content rather than the section's empty top padding.
    // A timed fade remains perceptible even when scrolling stops or jumps.
    document.querySelectorAll<HTMLElement>('main > section:not(.hero) > .wrap').forEach(surface => {
      const bounds = surface.getBoundingClientRect();
      gsap.set(surface, { opacity: bounds.bottom > 0 && bounds.top < innerHeight ? 1 : .08 });
      const fade = gsap.quickTo(surface, 'opacity', { duration: .75, ease: 'power2.out' });
      ScrollTrigger.create({
        trigger: surface, start: 'top 88%', end: 'bottom 12%',
        onToggle: trigger => fade(trigger.isActive ? 1 : .08),
        onRefresh: trigger => { if (trigger.isActive) fade(1); },
      });
    });
    const cleanups: (() => void)[] = [];
    document.querySelectorAll<HTMLButtonElement>('[data-role], [data-step]').forEach(button => {
      const listener = (event: MouseEvent) => {
        if (event.detail === 0) return;
        const target = button.hasAttribute('data-role') ? '.role-copy, #role-image' : '#workflow-image, #workflow-detail';
        gsap.fromTo(target, { opacity: .25 }, { opacity: 1, duration: .5, ease: 'power2.out', overwrite: true, clearProps: 'opacity' });
      };
      button.addEventListener('click', listener); cleanups.push(() => button.removeEventListener('click', listener));
    });
    return () => cleanups.forEach(cleanup => cleanup());
  });
  ScrollTrigger.refresh();
}

if (import.meta.hot) import.meta.hot.dispose(() => activeMedia?.revert());
