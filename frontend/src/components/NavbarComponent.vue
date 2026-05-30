<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container">
      <router-link class="navbar-brand fw-bold" to="/">🎯 Ивентус</router-link>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link class="nav-link" to="/feed">📋 Лента</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/events">📅 Каталог</router-link>
          </li>
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item">
            <router-link class="nav-link" to="/profile">👤 Профиль</router-link>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>