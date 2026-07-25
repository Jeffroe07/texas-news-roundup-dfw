const state = {
  stories: [],
  category: "All",
  posted: new Set(JSON.parse(localStorage.getItem("postedStories") || "[]"))
};

const categories = ["All","Breaking","Police","Fire","Traffic","Weather","Community","Sports"];

function escText(value){ return value || ""; }

function timeAgo(iso){
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds/60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds/3600)}h ago`;
  return `${Math.floor(seconds/86400)}d ago`;
}

function toast(message){
  const el = document.querySelector("#toast");
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 1800);
}

async function copyText(text){
  try{
    await navigator.clipboard.writeText(text);
    toast("Caption copied");
  }catch{
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
    toast("Caption copied");
  }
}

function renderCategories(){
  const nav = document.querySelector("#categories");
  nav.innerHTML = "";
  categories.forEach(name => {
    const btn = document.createElement("button");
    btn.textContent = name;
    btn.className = state.category === name ? "active" : "";
    btn.onclick = () => { state.category = name; renderCategories(); renderStories(); };
    nav.appendChild(btn);
  });
}

function getVisibleStories(){
  const q = document.querySelector("#search").value.trim().toLowerCase();
  const sort = document.querySelector("#sort").value;
  let items = state.stories.filter(s =>
    (state.category === "All" || s.category === state.category) &&
    (!q || `${s.title} ${s.summary} ${s.source}`.toLowerCase().includes(q))
  );
  items.sort((a,b) => sort === "oldest"
    ? new Date(a.published_at) - new Date(b.published_at)
    : new Date(b.published_at) - new Date(a.published_at));
  return items;
}

function renderStories(){
  const feed = document.querySelector("#feed");
  feed.innerHTML = "";
  const items = getVisibleStories();

  if(!items.length){
    feed.innerHTML = '<div class="empty">No stories match this view.</div>';
    return;
  }

  const template = document.querySelector("#storyTemplate");
  items.forEach(story => {
    const node = template.content.cloneNode(true);
    const card = node.querySelector(".card");
    const img = node.querySelector(".thumb");
    if(story.thumbnail){
      img.src = story.thumbnail;
      img.classList.add("visible");
      img.onerror = () => img.classList.remove("visible");
    }

    node.querySelector(".category").textContent = story.category;
    node.querySelector(".time").textContent = timeAgo(story.published_at);
    node.querySelector("h2").textContent = story.title;
    const summary = node.querySelector(".summary");
    summary.textContent = story.summary || "Open the original source for full details.";
    node.querySelector(".source").textContent = `Source: ${story.source}`;
    const caption = node.querySelector(".caption");
    caption.value = story.caption;

    node.querySelector(".copy").onclick = () => copyText(caption.value);
    node.querySelector(".share").onclick = async () => {
      if(navigator.share){
        try{
          await navigator.share({title: story.title, text: caption.value, url: story.url});
        }catch(e){}
      }else{
        await copyText(caption.value);
        window.open("https://www.facebook.com/", "_blank");
      }
    };
    const open = node.querySelector(".open");
    open.href = story.url;

    const posted = node.querySelector(".posted");
    if(state.posted.has(story.id)){
      posted.textContent = "Posted ✓";
      posted.classList.add("done");
    }
    posted.onclick = () => {
      if(state.posted.has(story.id)){
        state.posted.delete(story.id);
        posted.textContent = "Mark posted";
        posted.classList.remove("done");
      }else{
        state.posted.add(story.id);
        posted.textContent = "Posted ✓";
        posted.classList.add("done");
      }
      localStorage.setItem("postedStories", JSON.stringify([...state.posted]));
    };

    feed.appendChild(node);
  });
}

async function loadStories(){
  const refresh = document.querySelector("#refreshBtn");
  refresh.disabled = true;
  try{
    const response = await fetch(`data/stories.json?t=${Date.now()}`, {cache:"no-store"});
    if(!response.ok) throw new Error("News file unavailable");
    const data = await response.json();
    state.stories = data.stories || [];
    const updated = new Date(data.updated_at);
    document.querySelector("#updated").textContent =
      `${state.stories.length} stories · Updated ${updated.toLocaleString()}`;
    renderStories();
  }catch(error){
    document.querySelector("#feed").innerHTML =
      '<div class="empty">The news feed has not been generated yet. Run the GitHub Action once after setup.</div>';
  }finally{
    refresh.disabled = false;
  }
}

document.querySelector("#refreshBtn").onclick = loadStories;
document.querySelector("#search").addEventListener("input", renderStories);
document.querySelector("#sort").addEventListener("change", renderStories);
renderCategories();
loadStories();

if("serviceWorker" in navigator){
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js"));
}
